from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    detail: str | None = None
    category: str | None = None
    price: Decimal | None = None
    imageUrl: str | None = None
    images: list[str] = []
    tags: list[str] = []


def product_dict(product) -> dict:
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


@router.get("")
async def list_products(db: AsyncSession = Depends(get_db)):
    products = await ProductService(db).list_products()
    return [product_dict(product) for product in products if product.status == "active" and product.seller_id is not None]


@router.post("")
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()
    data["image_url"] = data.pop("imageUrl", None)
    return product_dict(await ProductService(db).create_product(data))


@router.get("/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await ProductService(db).get_product(product_id)
    return product_dict(product)
