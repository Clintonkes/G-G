from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.session import get_db
from models.appointment import Appointment
from models.notification import NotificationType
from models.payment import Payment, PaymentStatus
from models.property import Property, PropertyStatus
from models.user import User
from schemas.payment import PaymentResponse
from schemas.property import PropertyResponse
from schemas.user import UserResponse
from services.dependencies import require_admin
from services.notification_service import create_notification


router = APIRouter()


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict[str, int | float]:
    upcoming_cutoff = datetime.utcnow() + timedelta(days=7)
    return {
        "total_users": db.scalar(select(func.count(User.id))) or 0,
        "total_properties": db.scalar(select(func.count(Property.id))) or 0,
        "active_listings": db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.ACTIVE)) or 0,
        "pending_verifications": db.scalar(select(func.count(Property.id)).where(Property.status == PropertyStatus.PENDING_VERIFICATION)) or 0,
        "total_transactions": db.scalar(select(func.count(Payment.id)).where(Payment.status == PaymentStatus.SUCCESS)) or 0,
        "total_revenue": db.scalar(select(func.coalesce(func.sum(Payment.platform_fee), 0)).where(Payment.status == PaymentStatus.SUCCESS)) or 0,
        "upcoming_appointments": db.scalar(select(func.count(Appointment.id)).where(Appointment.scheduled_date <= upcoming_cutoff)) or 0,
        "pending_remittances": db.scalar(select(func.count(Payment.id)).where(Payment.landlord_remitted.is_(False), Payment.status == PaymentStatus.SUCCESS)) or 0,
    }


@router.get("/properties", response_model=list[PropertyResponse])
def list_all_properties(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[PropertyResponse]:
    items = db.scalars(select(Property).order_by(Property.created_at.desc())).all()
    return [PropertyResponse.model_validate(item) for item in items]


@router.post("/properties/{property_id}/verify", response_model=PropertyResponse)
def verify_property(property_id: str, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> PropertyResponse:
    property_record = db.get(Property, property_id)
    if not property_record:
        raise HTTPException(status_code=404, detail="Property not found.")
    property_record.status = PropertyStatus.ACTIVE
    property_record.is_verified = True
    property_record.verified_at = datetime.utcnow()
    create_notification(
        db,
        property_record.landlord_id,
        "Property verified",
        f"{property_record.title} is now live on G & G Homes.",
        NotificationType.VERIFICATION,
    )
    db.commit()
    db.refresh(property_record)
    return PropertyResponse.model_validate(property_record)


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[UserResponse]:
    items = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [UserResponse.model_validate(item) for item in items]


@router.get("/remittances", response_model=list[PaymentResponse])
def pending_remittances(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[PaymentResponse]:
    items = db.scalars(
        select(Payment).where(Payment.status == PaymentStatus.SUCCESS, Payment.landlord_remitted.is_(False)).order_by(Payment.created_at.desc())
    ).all()
    return [PaymentResponse.model_validate(item) for item in items]


@router.post("/remittances/{payment_id}", response_model=PaymentResponse)
def mark_as_remitted(
    payment_id: str,
    remittance_reference: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> PaymentResponse:
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
    payment.landlord_remitted = True
    payment.remittance_reference = remittance_reference
    payment.remitted_at = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return PaymentResponse.model_validate(payment)
