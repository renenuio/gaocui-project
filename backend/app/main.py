from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)


from app.api.v1 import ai, auth, lead, notification, payment, product, seller, uploads, user, vip
from app.core.config import settings
from app.core.redis import close_redis
from app.db.base import Base
from app.db.schema_upgrade import ensure_production_columns
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        if settings.ENABLE_PGVECTOR_EXTENSION:
            await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.run_sync(Base.metadata.create_all)
        await ensure_production_columns(conn)
    yield
    await close_redis()



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

app.include_router(user.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(product.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai.router, prefix=settings.API_V1_PREFIX)
app.include_router(vip.router, prefix=settings.API_V1_PREFIX)
app.include_router(payment.router, prefix=settings.API_V1_PREFIX)
app.include_router(lead.router, prefix=settings.API_V1_PREFIX)
app.include_router(seller.router, prefix=settings.API_V1_PREFIX)
app.include_router(notification.router, prefix=settings.API_V1_PREFIX)
app.include_router(uploads.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.PROJECT_NAME}
