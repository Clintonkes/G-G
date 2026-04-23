from fastapi import APIRouter, Depends, File, UploadFile

from app.models.user import User
from app.services.dependencies import get_current_user
from app.services.upload_service import upload_file


router = APIRouter()


@router.post("")
async def upload_asset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    url = await upload_file(file)
    return {"url": url, "uploaded_by": current_user.id}
