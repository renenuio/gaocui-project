from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_seller
from app.db.session import get_db
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.product import Product
from app.models.user import User
from app.services.embedding_service import semantic_embedding_service

router = APIRouter(prefix="/seller", tags=["seller"])


class SellerProductPayload(BaseModel):
    name: str
    description: str | None = None
    detail: str | None = None
    category: str = "jade"
    price: Decimal | None = None
    imageUrl: str | None = None
    images: list[str] = []
    tags: list[str] = []
    status: str = "active"


class UploadPayload(BaseModel):
    filename: str | None = None
    image: str


class AIGeneratePayload(BaseModel):
    images: list[str]


class LeadStatusPayload(BaseModel):
    status: str


def product_dict(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "detail": product.detail,
        "category": product.category,
        "price": float(product.price) if product.price is not None else None,
        "sellerId": product.seller_id,
        "status": product.status,
        "imageUrl": product.image_url,
        "images": product.images or ([product.image_url] if product.image_url else []),
        "tags": product.tags or [],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def mask_email(value: str | None) -> str | None:
    if not value or "@" not in value:
        return value
    _, domain = value.split("@", 1)
    return f"****@{domain}"


def lead_dict(lead: Lead, is_vip: bool) -> dict[str, Any]:
    return {
        "id": lead.id,
        "email": lead.email if is_vip else mask_email(lead.email),
        "buyerEmail": lead.email if is_vip else mask_email(lead.email),
        "source": lead.source,
        "note": lead.note,
        "status": lead.status,
        "product_id": lead.product_id,
        "seller_id": lead.seller_id,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


def seller_limits(seller: User) -> dict[str, Any]:
    is_vip = seller.membership == "vip"
    return {
        "sellerId": seller.id,
        "email": seller.email,
        "membership": seller.membership,
        "isVip": is_vip,
        "productLimit": 100 if is_vip else 2,
        "leadVisibility": "full" if is_vip else "masked",
        "priorityWeight": "high" if is_vip else "low",
    }


async def active_product_count(db: AsyncSession, seller: User) -> int:
    value = await db.scalar(
        select(func.count()).select_from(Product).where(Product.seller_id == seller.id, Product.status == "active")
    )
    return int(value or 0)


@router.get("/profile")
async def profile(seller: User = Depends(current_seller)):
    return {
        **seller_limits(seller),
        "vipStartAt": None,
        "vipEndAt": "2026-12-31" if seller.membership == "vip" else None,
        "notificationSettings": {"web": True, "email": True},
    }


@router.get("/entitlements")
async def entitlements(db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    limits = seller_limits(seller)
    return {
        **limits,
        "activeProductCount": await active_product_count(db, seller),
        "todayPublishedCount": await active_product_count(db, seller),
        "plans": [
            {"code": "vip_12m", "name": "VIP会员（12个月）", "price": 2999},
            {"code": "vip_6m", "name": "VIP会员（6个月）", "price": 1688},
        ],
    }


@router.get("/quota")
async def quota(db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    limits = seller_limits(seller)
    count = await active_product_count(db, seller)
    return {"productLimit": limits["productLimit"], "activeProductCount": count, "remaining": max(limits["productLimit"] - count, 0)}


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    limits = seller_limits(seller)
    product_count = await active_product_count(db, seller)
    lead_count = await db.scalar(select(func.count()).select_from(Lead).where(Lead.seller_id == seller.id))
    result = await db.execute(select(Lead).where(Lead.seller_id == seller.id).order_by(Lead.created_at.desc()).limit(4))
    return {
        "productCount": product_count,
        "productLimit": limits["productLimit"],
        "todayLeadCount": int(lead_count or 0),
        "totalLeadCount": int(lead_count or 0),
        "recentLeads": [lead_dict(lead, limits["isVip"]) for lead in result.scalars().all()],
        "seller": limits,
    }


@router.get("/products")
async def products(db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    result = await db.execute(select(Product).where(Product.seller_id == seller.id).order_by(Product.created_at.desc()))
    return [product_dict(product) for product in result.scalars().all()]


@router.post("/products")
async def create_product(payload: SellerProductPayload, db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    count = await active_product_count(db, seller)
    if payload.status == "active" and count >= seller_limits(seller)["productLimit"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Product quota exceeded")
    product = Product(**_product_payload(payload, seller.id))
    product.embedding = semantic_embedding_service.embed(_product_embedding_text(product))
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product_dict(product)


@router.patch("/products/{product_id}")
async def update_product(product_id: int, payload: SellerProductPayload, db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    product = await _seller_product(db, product_id, seller)
    for key, value in _product_payload(payload, seller.id).items():
        setattr(product, key, value)
    product.embedding = semantic_embedding_service.embed(_product_embedding_text(product))
    await db.commit()
    await db.refresh(product)
    return product_dict(product)


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    product = await _seller_product(db, product_id, seller)
    await db.delete(product)
    await db.commit()
    return {"ok": True}


@router.post("/products/upload")
async def upload_product_image(payload: UploadPayload, seller: User = Depends(current_seller)):
    return {
        "imageId": f"seller-{seller.id}-{int(datetime.utcnow().timestamp())}",
        "imageUrl": payload.image,
        "filename": payload.filename or "upload.jpg",
    }


@router.post("/products/ai-generate")
async def ai_generate_product(payload: AIGeneratePayload, seller: User = Depends(current_seller)):
    if not payload.images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one image is required")
    return {
        "name": "翡翠商品",
        "description": "根据上传图片生成的翡翠商品简介，请商家确认后发布。",
        "detail": "系统已接收商家上传图片，并生成可编辑商品详情。发布前请核对种水、颜色、瑕疵、尺寸和证书信息。",
        "category": "jade",
        "price": None,
        "imageUrl": payload.images[0],
        "images": payload.images,
        "tags": ["翡翠", "天然A货", "待商家确认"],
        "status": "active",
    }


@router.get("/leads")
async def leads(db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    result = await db.execute(select(Lead).where(Lead.seller_id == seller.id).order_by(Lead.created_at.desc()))
    return [lead_dict(lead, seller.membership == "vip") for lead in result.scalars().all()]


@router.get("/leads/{lead_id}")
async def lead_detail(lead_id: int, db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    lead = await _seller_lead(db, lead_id, seller)
    return lead_dict(lead, seller.membership == "vip")


@router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: int, payload: LeadStatusPayload, db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    lead = await _seller_lead(db, lead_id, seller)
    if payload.status not in {"pending", "contacted"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid lead status")
    lead.status = payload.status
    await db.commit()
    await db.refresh(lead)
    return lead_dict(lead, seller.membership == "vip")


@router.get("/orders")
async def orders(seller: User = Depends(current_seller)):
    return []


@router.post("/upgrade-intent")
async def upgrade_intent(seller: User = Depends(current_seller)):
    return {"ok": True, "sellerId": seller.id}


async def _seller_product(db: AsyncSession, product_id: int, seller: User) -> Product:
    product = await db.get(Product, product_id)
    if not product or product.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def _seller_lead(db: AsyncSession, lead_id: int, seller: User) -> Lead:
    lead = await db.get(Lead, lead_id)
    if not lead or lead.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


def _product_payload(payload: SellerProductPayload, seller_id: int) -> dict[str, Any]:
    return {
        "name": payload.name,
        "description": payload.description,
        "detail": payload.detail,
        "category": "jade",
        "price": payload.price,
        "seller_id": seller_id,
        "status": payload.status,
        "image_url": payload.imageUrl or (payload.images[0] if payload.images else None),
        "images": payload.images,
        "tags": payload.tags,
    }


def _product_embedding_text(product: Product) -> str:
    return " ".join(str(value or "") for value in [product.name, product.description, product.detail, product.category])
