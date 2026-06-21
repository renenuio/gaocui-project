from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_products(self) -> list[Product]:
        result = await self.db.execute(select(Product).order_by(Product.created_at.desc()))
        return list(result.scalars().all())

    async def create_product(self, data: dict) -> Product:
        product = Product(**data)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_product(self, product_id: int) -> Product:
        product = await self.db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

