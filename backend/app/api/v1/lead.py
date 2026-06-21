from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.lead import Lead
from app.models.notification import Notification
from app.models.product import Product

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCreate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    source: str | None = None
    note: str | None = None
    product_id: int


@router.post("")
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, payload.product_id)
    if not product or product.status != "active" or product.seller_id is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    data = payload.model_dump()
    data["seller_id"] = product.seller_id
    data["source"] = data.get("source") or product.name
    lead = Lead(**data)
    db.add(lead)
    db.add(Notification(seller_id=product.seller_id, type="new_lead", content=f"有新客户留资：{lead.note or product.name}"))
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("")
async def list_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    return result.scalars().all()
