from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.vip_service import VIPService

router = APIRouter(prefix="/vip", tags=["vip"])


@router.get("/plans")
async def list_plans() -> dict[str, list[dict[str, str | int]]]:
    return {
        "plans": [
            {"code": "monthly", "name": "Monthly VIP", "price_cents": 1999},
            {"code": "yearly", "name": "Yearly VIP", "price_cents": 19900},
        ]
    }


@router.get("/status/{user_id}")
async def vip_status(user_id: int, db: AsyncSession = Depends(get_db)):
    return await VIPService(db).get_status(user_id)

