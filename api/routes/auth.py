from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from core.security import create_access_token, get_password_hash, verify_password
from db.session import get_db
from models.subscription import Subscription, SubscriptionPlan
from models.user import User
from schemas.auth import ForgotPasswordRequest, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services.email_service import send_email
from services.dependencies import get_current_user
from services.helpers import generate_id


router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing_user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user = User(
        id=generate_id(),
        full_name=payload.full_name,
        email=payload.email.lower(),
        phone_number=payload.phone_number,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        id_document_url=payload.id_document_url,
        id_verified=False,
    )
    subscription = Subscription(
        id=generate_id(),
        user_id=user.id,
        plan=SubscriptionPlan.FREE,
        is_active=True,
    )
    db.add(user)
    db.add(subscription)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user:
        await send_email(
            [user.email],
            "Reset your G & G Homes password",
            "<p>We received a password reset request. Contact support or implement token-based reset flow before production launch.</p>",
        )
    return {"message": "If the email exists, password reset instructions have been sent."}
