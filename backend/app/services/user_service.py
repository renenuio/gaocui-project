import base64
import hashlib
import hmac
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import seller_token
from app.models.user import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: dict) -> User:
        existing = await self.db.execute(select(User).where(User.email == data["email"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        password = data.pop("password")
        user = User(**data, hashed_password=self._hash_password(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return self._auth_response(user)

    async def login(self, email: str, password: str) -> dict[str, str | int]:
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not self._verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return self._auth_response(user)

    def _auth_response(self, user: User) -> dict[str, str | int | bool]:
        return {
            "access_token": seller_token(user),
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "membership": user.membership,
            "isVip": user.membership == "vip",
        }

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return "pbkdf2_sha256$120000$%s$%s" % (
            base64.b64encode(salt).decode(),
            base64.b64encode(digest).decode(),
        )

    def _verify_password(self, password: str, stored: str) -> bool:
        try:
            algorithm, iterations, salt, digest = stored.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            expected = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                base64.b64decode(salt.encode()),
                int(iterations),
            )
            return hmac.compare_digest(base64.b64encode(expected).decode(), digest)
        except Exception:
            return False
