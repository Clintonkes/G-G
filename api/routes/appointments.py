from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from models.appointment import Appointment, AppointmentOutcome, AppointmentStatus
from models.notification import NotificationType
from models.property import Property, PropertyStatus
from models.subscription import SubscriptionPlan
from models.user import User, UserRole
from schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from services.dependencies import get_current_user
from services.helpers import generate_id
from services.notification_service import create_notification


router = APIRouter()
EDIT_WINDOW = timedelta(hours=48)
OPEN_APPOINTMENT_STATUSES = {AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED}


def notify_once_per_status(db: Session, appointment: Appointment, title: str, message: str) -> None:
    recipient_ids = {appointment.tenant_id, appointment.landlord_id}
    for recipient_id in recipient_ids:
        create_notification(db, recipient_id, title, message, NotificationType.APPOINTMENT)


def expire_unattended_appointments(db: Session, appointments: list[Appointment]) -> None:
    now = datetime.utcnow()
    changed = False
    for appointment in appointments:
        if appointment.status not in OPEN_APPOINTMENT_STATUSES or appointment.scheduled_date >= now:
            continue

        property_record = db.get(Property, appointment.property_id)
        appointment.status = AppointmentStatus.INVALID
        appointment.admin_notes = appointment.admin_notes or "Appointment date passed before attendance was confirmed."
        notify_once_per_status(
            db,
            appointment,
            "Appointment missed",
            f"The appointment for {property_record.title if property_record else 'a listed property'} has passed without admin attendance confirmation. Please set another appointment date.",
        )
        changed = True

    if changed:
        db.commit()


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AppointmentResponse]:
    if current_user.role == UserRole.ADMIN:
        items = db.scalars(select(Appointment).order_by(Appointment.created_at.desc())).all()
    elif current_user.role == UserRole.LANDLORD:
        items = db.scalars(select(Appointment).where(Appointment.landlord_id == current_user.id).order_by(Appointment.created_at.desc())).all()
    else:
        items = db.scalars(select(Appointment).where(Appointment.tenant_id == current_user.id).order_by(Appointment.created_at.desc())).all()
    expire_unattended_appointments(db, items)
    return [AppointmentResponse.model_validate(item) for item in items]


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AppointmentResponse:
    property_record = db.get(Property, payload.property_id)
    if not property_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not available.")

    is_listing_verification = (
        current_user.id == property_record.landlord_id
        and property_record.status == PropertyStatus.PENDING_VERIFICATION
    )
    is_public_inspection = property_record.status == PropertyStatus.ACTIVE
    if not is_listing_verification and not is_public_inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not available for appointments.")
    if payload.scheduled_date <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date must be in the future.")

    existing = db.scalar(
        select(Appointment).where(
            Appointment.property_id == property_record.id,
            Appointment.tenant_id == current_user.id,
            Appointment.status.in_(list(OPEN_APPOINTMENT_STATUSES)),
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This property already has an active appointment.")

    if is_public_inspection:
        subscription = current_user.subscription
        current_month = datetime.utcnow().month
        if subscription and subscription.plan == SubscriptionPlan.FREE and subscription.appointments_used_this_month >= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan users are limited to 1 inspection request per month. Upgrade to continue.",
            )
    else:
        subscription = None
        current_month = datetime.utcnow().month

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
        property_record.landlord_id if is_public_inspection else current_user.id,
        "New inspection request" if is_public_inspection else "Verification appointment fixed",
        f"A new inspection request has been made for {property_record.title}."
        if is_public_inspection
        else f"Your verification appointment for {property_record.title} has been fixed for {payload.scheduled_date.strftime('%b %d, %Y %I:%M %p')}.",
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

    property_record = db.get(Property, appointment.property_id)
    updates = payload.model_dump(exclude_unset=True)

    if current_user.role != UserRole.ADMIN:
        blocked_fields = {"status", "outcome", "admin_notes"}.intersection(updates)
        if blocked_fields:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an admin can update appointment status or attendance.")
        if "scheduled_date" in updates:
            if payload.scheduled_date and payload.scheduled_date <= datetime.utcnow():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date must be in the future.")
            if appointment.status not in OPEN_APPOINTMENT_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending or confirmed appointments can be rescheduled.")
            if datetime.utcnow() > appointment.scheduled_date - EDIT_WINDOW:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment dates can only be edited at least 48 hours before the scheduled time.")

    previous_status = appointment.status
    previous_date = appointment.scheduled_date
    for field, value in updates.items():
        setattr(appointment, field, value)

    if payload.scheduled_date and payload.scheduled_date != previous_date:
        notify_once_per_status(
            db,
            appointment,
            "Appointment date updated",
            f"The appointment for {property_record.title if property_record else 'a listed property'} has been moved to {payload.scheduled_date.strftime('%b %d, %Y %I:%M %p')}.",
        )

    if payload.outcome == AppointmentOutcome.INTERESTED:
        payment_link = f"{current_user.id}:{appointment.property_id}"
        create_notification(
            db,
            appointment.tenant_id,
            "Payment link ready",
            f"You marked interest in {property_record.title}. Use the payment flow in your dashboard to complete rent payment. Ref: {payment_link}",
            NotificationType.PAYMENT,
        )

    if payload.status and payload.status != previous_status:
        if payload.status == AppointmentStatus.COMPLETED:
            notify_once_per_status(
                db,
                appointment,
                "Appointment attended",
                f"Admin marked the appointment for {property_record.title if property_record else 'a listed property'} as attended.",
            )
        if payload.status in {AppointmentStatus.NO_SHOW, AppointmentStatus.INVALID}:
            notify_once_per_status(
                db,
                appointment,
                "Appointment missed",
                f"Admin marked the appointment for {property_record.title if property_record else 'a listed property'} as missed. Please set another appointment date.",
            )

    db.commit()
    db.refresh(appointment)
    return AppointmentResponse.model_validate(appointment)
