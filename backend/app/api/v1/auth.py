from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_seller
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def me(
    db: AsyncSession = Depends(get_db),
    seller: User = Depends(current_seller),
):
    return {
        "sellerId": seller.id,
        "email": seller.email,
        "membership": seller.membership,
        "isVip": seller.membership == "vip",
    }
