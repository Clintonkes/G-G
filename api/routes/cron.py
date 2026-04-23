from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from models.notification import NotificationType
from models.payment import Payment, PaymentStatus
from models.property import Property
from models.user import User
from services.dependencies import verify_cron_secret
from services.email_service import send_email
from services.notification_service import create_notification


router = APIRouter()


@router.post("/reminders", dependencies=[Depends(verify_cron_secret)])
async def send_rental_reminders(db: Session = Depends(get_db)) -> dict[str, int]:
    today = date.today()
    reminders_sent = 0
    payments = db.scalars(
        select(Payment).where(Payment.status == PaymentStatus.SUCCESS, Payment.tenancy_end_date.is_not(None))
    ).all()

    for payment in payments:
        days_remaining = (payment.tenancy_end_date - today).days if payment.tenancy_end_date else None
        if days_remaining not in {90, 60, 30}:
            continue
        user = db.get(User, payment.payer_id)
        property_record = db.get(Property, payment.property_id) if payment.property_id else None
        if not user:
            continue
        address = property_record.address if property_record else "your tenancy"
        title = f"Tenancy renewal reminder: {days_remaining} days left"
        message = f"Your tenancy at {address} expires in {days_remaining} days."
        create_notification(db, user.id, title, message, NotificationType.REMINDER)
        await send_email([user.email], title, f"<p>{message}</p>")
        reminders_sent += 1
        if days_remaining == 30 and property_record:
            landlord = db.get(User, property_record.landlord_id)
            if landlord:
                create_notification(
                    db,
                    landlord.id,
                    "Tenant renewal window opened",
                    f"A tenancy at {address} expires in 30 days.",
                    NotificationType.REMINDER,
                )
                reminders_sent += 1
    db.commit()
    return {"reminders_sent": reminders_sent}
