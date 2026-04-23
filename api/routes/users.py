from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from models.user import User
from schemas.user import UserProfileUpdate, UserResponse
from services.dependencies import get_current_user


router = APIRouter()


@router.get("/me", response_model=UserResponse)
def current_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    if payload.email and payload.email.lower() != current_user.email:
        existing = db.scalar(select(User).where(User.email == payload.email.lower()))
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "email" and value:
            value = value.lower()
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
