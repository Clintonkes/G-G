import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, UploadFile, status

from core.config import settings


def _cloudinary_configured() -> bool:
    return bool(
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )


if _cloudinary_configured():
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


async def upload_file(file: UploadFile) -> str:
    if not _cloudinary_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "File storage is not configured. "
                "Add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and "
                "CLOUDINARY_API_SECRET to the Railway environment variables, "
                "then redeploy."
            ),
        )

    try:
        result = cloudinary.uploader.upload(file.file, resource_type="auto", folder="gghomes")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary upload failed. Confirm the Railway Cloudinary environment variables are correct.",
        ) from exc

    secure_url = result.get("secure_url")
    if not secure_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloudinary did not return a secure upload URL.",
        )
    return secure_url
