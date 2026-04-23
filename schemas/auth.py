from pydantic import BaseModel, EmailStr, Field, field_validator

from models.user import UserRole
from schemas.common import ORMModel


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    email: EmailStr
    phone_number: str = Field(min_length=11, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.TENANT
    id_document_url: str | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_nigerian_phone(cls, value: str) -> str:
        normalized = value.replace(" ", "").replace("-", "")
        if not (normalized.startswith("+234") or normalized.startswith("0")):
            raise ValueError("Use a valid Nigerian phone number.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(character.isupper() for character in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must include at least one number.")
        if value.isalnum():
            raise ValueError("Password must include at least one special character.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(ORMModel):
    id: str
    full_name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    is_active: bool
    id_verified: bool
    id_document_url: str | None = None


TokenResponse.model_rebuild()
