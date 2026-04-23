from pathlib import Path
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import settings


if settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


async def upload_file(file: UploadFile) -> str:
    if settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret:
        result = cloudinary.uploader.upload(file.file, resource_type="auto", folder="gghomes")
        return result["secure_url"]

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    suffix = Path(file.filename or "").suffix or ".bin"
    target = uploads_dir / f"{uuid4()}{suffix}"
    content = await file.read()
    target.write_bytes(content)
    return f"/{target.as_posix()}"
