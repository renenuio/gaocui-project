from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import lead, notification, product, user, vip_order  # noqa: E402,F401
