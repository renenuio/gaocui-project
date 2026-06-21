from sqlalchemy.ext.asyncio import AsyncConnection


async def ensure_production_columns(conn: AsyncConnection) -> None:
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS membership VARCHAR(20) NOT NULL DEFAULT 'free'",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS detail TEXT",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS seller_id INTEGER",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url VARCHAR(1000)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS images JSON",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS tags JSON",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS product_id INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS seller_id INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'pending'",
    ]
    for statement in statements:
        await conn.exec_driver_sql(statement)
