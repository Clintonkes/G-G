from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import ORMModel


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3)
    email: EmailStr | None = None
    phone_number: str | None = None
    id_document_url: str | None = None
    role: UserRole | None = None


class UserResponse(ORMModel):
    id: str
    full_name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    is_active: bool
    id_verified: bool
    id_document_url: str | None = None
