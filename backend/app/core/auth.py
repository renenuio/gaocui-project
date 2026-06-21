import base64
import hashlib
import hmac
import json

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


def seller_token(user: User) -> str:
    payload = {"user_id": user.id, "email": user.email}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_secret(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def _secret() -> bytes:
    value = settings.SECRET_KEY or settings.PROJECT_NAME
    return value.encode()


def _decode_token(token: str) -> dict:
    try:
        encoded, signature = token.rsplit(".", 1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid seller token") from exc
    expected = hmac.new(_secret(), encoded.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid seller token")
    padded = encoded + "=" * (-len(encoded) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid seller token") from exc


async def current_seller(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing seller token")

    payload = _decode_token(authorization.split(" ", 1)[1])
    result = await db.execute(select(User).where(User.id == int(payload["user_id"]), User.email == payload["email"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Seller not found")
    return user
