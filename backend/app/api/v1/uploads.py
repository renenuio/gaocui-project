from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import current_seller
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


class ImageUploadPayload(BaseModel):
    filename: str | None = None
    image: str


@router.post("/images")
async def upload_image(payload: ImageUploadPayload, seller: User = Depends(current_seller)):
    return {
        "imageId": f"seller-{seller.id}-image",
        "imageUrl": payload.image,
        "filename": payload.filename or "upload.jpg",
    }
