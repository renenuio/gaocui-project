from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["payments"])


class PaymentCreate(BaseModel):
    user_id: int
    plan_code: str
    provider: str = "placeholder"


@router.post("/checkout")
async def create_checkout(payload: PaymentCreate) -> dict[str, str | int]:
    return {
        "status": "pending",
        "message": "Payment provider integration placeholder",
        "user_id": payload.user_id,
        "plan_code": payload.plan_code,
    }

