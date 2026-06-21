from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    seller_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
