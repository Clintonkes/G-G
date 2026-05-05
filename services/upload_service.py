from pathlib import Path
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from core.config import settings


if settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


async def upload_file(file: UploadFile) -> str:
    if settings.cloudinary_cloud_name and settings.cloudinary_api_key and settings.cloudinary_api_secret:
        try:
            result = cloudinary.uploader.upload(file.file, resource_type="auto", folder="gghomes")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Cloudinary upload failed. Confirm the Railway Cloudinary environment variables are correct.",
            ) from exc
        secure_url = result.get("secure_url")
        if not secure_url:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Cloudinary did not return a secure upload URL.")
        return secure_url

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    suffix = Path(file.filename or "").suffix or ".bin"
    target = uploads_dir / f"{uuid4()}{suffix}"
    content = await file.read()
    target.write_bytes(content)
    return f"/{target.as_posix()}"
