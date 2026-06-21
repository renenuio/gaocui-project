from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vip_order import VIPOrder


class VIPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_status(self, user_id: int) -> dict:
        result = await self.db.execute(
            select(VIPOrder)
            .where(VIPOrder.user_id == user_id, VIPOrder.status == "paid")
            .order_by(VIPOrder.created_at.desc())
            .limit(1)
        )
        order = result.scalar_one_or_none()
        return {"user_id": user_id, "is_vip": order is not None, "latest_order_id": order.id if order else None}

