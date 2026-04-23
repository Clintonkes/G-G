from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.appointment import Appointment, AppointmentOutcome, AppointmentStatus
from app.models.notification import NotificationType
from app.models.property import Property, PropertyStatus
from app.models.subscription import SubscriptionPlan
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.schemas.payment import PaymentInitializeRequest
from app.services.dependencies import get_current_user
from app.services.helpers import generate_id
from app.services.notification_service import create_notification


router = APIRouter()


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AppointmentResponse]:
    if current_user.role == UserRole.ADMIN:
        items = db.scalars(select(Appointment).order_by(Appointment.created_at.desc())).all()
    elif current_user.role == UserRole.LANDLORD:
        items = db.scalars(select(Appointment).where(Appointment.landlord_id == current_user.id).order_by(Appointment.created_at.desc())).all()
    else:
        items = db.scalars(select(Appointment).where(Appointment.tenant_id == current_user.id).order_by(Appointment.created_at.desc())).all()
    return [AppointmentResponse.model_validate(item) for item in items]


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AppointmentResponse:
    property_record = db.get(Property, payload.property_id)
    if not property_record or property_record.status != PropertyStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not available.")

    subscription = current_user.subscription
    current_month = datetime.utcnow().month
    if subscription and subscription.plan == SubscriptionPlan.FREE and subscription.appointments_used_this_month >= 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Free plan users are limited to 1 inspection request per month. Upgrade to continue.",
        )

    appointment = Appointment(
        id=generate_id(),
        tenant_id=current_user.id,
        property_id=property_record.id,
        landlord_id=property_record.landlord_id,
        scheduled_date=payload.scheduled_date,
        tenant_notes=payload.tenant_notes,
    )
    db.add(appointment)
    if subscription:
        if subscription.updated_at.month != current_month:
            subscription.appointments_used_this_month = 0
        subscription.appointments_used_this_month += 1
    create_notification(
        db,
        property_record.landlord_id,
        "New inspection request",
        f"A new inspection request has been made for {property_record.title}.",
        NotificationType.APPOINTMENT,
    )
    db.commit()
    db.refresh(appointment)
    return AppointmentResponse.model_validate(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: str,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AppointmentResponse:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    is_owner = current_user.role == UserRole.ADMIN or appointment.landlord_id == current_user.id or appointment.tenant_id == current_user.id
    if not is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot update this appointment.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    if payload.outcome == AppointmentOutcome.INTERESTED:
        property_record = db.get(Property, appointment.property_id)
        payment_link = f"{current_user.id}:{appointment.property_id}"
        create_notification(
            db,
            appointment.tenant_id,
            "Payment link ready",
            f"You marked interest in {property_record.title}. Use the payment flow in your dashboard to complete rent payment. Ref: {payment_link}",
            NotificationType.PAYMENT,
        )

    db.commit()
    db.refresh(appointment)
    return AppointmentResponse.model_validate(appointment)
