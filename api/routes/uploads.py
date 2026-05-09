from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from models.user import User
from services.ai_service import validate_property_image
from services.dependencies import get_current_user
from services.upload_service import upload_file


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".avif", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv", ".flv", ".wmv"}

router = APIRouter()


def _classify_file(file: UploadFile) -> str:
    """Return 'image', 'video', or 'other' based on content-type and extension."""
    content_type = (file.content_type or "").lower()
    ext = Path(file.filename or "").suffix.lower()

    if content_type.startswith("image/") or ext in IMAGE_EXTENSIONS:
        return "image"
    if content_type.startswith("video/") or ext in VIDEO_EXTENSIONS:
        return "video"
    return "other"


@router.post("")
async def upload_asset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    url = await upload_file(file)

    file_kind = _classify_file(file)

    if file_kind == "image":
        is_valid = await validate_property_image(url)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "This photo does not appear to show a building, room, or property. "
                    "Please upload actual property photos only."
                ),
            )
    # Videos and documents are accepted without AI content validation.
    # Video frames cannot be checked via the Vision API; rely on landlord responsibility.

    return {"url": url, "uploaded_by": current_user.id}
