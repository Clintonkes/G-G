from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from models.user import User
from services.ai_service import validate_property_image
from services.dependencies import get_current_user
from services.upload_service import upload_file


router = APIRouter()


@router.post("")
async def upload_asset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    url = await upload_file(file)

    # Only run AI content check on images — videos and documents are not validated.
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        is_valid = await validate_property_image(url)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "This photo does not appear to show a building, room, or property. "
                    "Please upload actual property photos only."
                ),
            )

    return {"url": url, "uploaded_by": current_user.id}
