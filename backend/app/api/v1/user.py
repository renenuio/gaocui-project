from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    return await UserService(db).create_user(payload.model_dump())


@router.post("/login")
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    return await UserService(db).login(payload.email, payload.password)


@router.get("/me")
async def me() -> dict[str, str]:
    return {"message": "Auth dependency placeholder"}

