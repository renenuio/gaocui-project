from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_seller
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


def notification_dict(item: Notification) -> dict:
    return {
        "id": item.id,
        "type": item.type,
        "content": item.content,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "readAt": item.read_at.isoformat() if item.read_at else None,
    }


@router.get("")
async def list_notifications(db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    result = await db.execute(
        select(Notification).where(Notification.seller_id == seller.id).order_by(Notification.created_at.desc())
    )
    return [notification_dict(item) for item in result.scalars().all()]


@router.patch("/{notification_id}/read")
async def mark_read(notification_id: int, db: AsyncSession = Depends(get_db), seller: User = Depends(current_seller)):
    item = await db.get(Notification, notification_id)
    if not item or item.seller_id != seller.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    item.read_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)
    return notification_dict(item)
