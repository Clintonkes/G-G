from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from db.session import get_db
from models.notification import NotificationType
from models.payment import Payment, PaymentStatus
from models.property import Property, PropertyStatus
from models.user import User
from schemas.payment import PaymentInitializeRequest, PaymentLinkResponse, PaymentResponse, PaymentVerifyRequest
from services.dependencies import get_current_user
from services.email_service import send_email
from services.flutterwave_service import initialize_flutterwave_payment, verify_flutterwave_payment
from services.helpers import calculate_platform_fee, generate_id
from services.notification_service import create_notification


router = APIRouter()


@router.get("", response_model=list[PaymentResponse])
def list_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[PaymentResponse]:
    items = db.scalars(select(Payment).where(Payment.payer_id == current_user.id).order_by(Payment.created_at.desc())).all()
    return [PaymentResponse.model_validate(item) for item in items]


@router.post("/initialize", response_model=PaymentLinkResponse)
async def initialize_payment(
    payload: PaymentInitializeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentLinkResponse:
    property_record = db.get(Property, payload.property_id) if payload.property_id else None
    if payload.property_id and (not property_record or property_record.status != PropertyStatus.ACTIVE):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not available for payment.")

    platform_fee = calculate_platform_fee(payload.gross_amount)
    payment = Payment(
        id=generate_id(),
        payer_id=current_user.id,
        property_id=payload.property_id,
        payment_type=payload.payment_type,
        gross_amount=payload.gross_amount,
        platform_fee=platform_fee,
        net_amount=payload.gross_amount - platform_fee,
        flutterwave_reference=f"GGH-{generate_id()}",
        tenancy_start_date=payload.tenancy_start_date,
        tenancy_end_date=payload.tenancy_end_date,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    checkout_url = await initialize_flutterwave_payment(
        email=current_user.email,
        name=current_user.full_name,
        amount=payload.gross_amount,
        tx_ref=payment.flutterwave_reference,
        redirect_url=f"{settings.frontend_url}/payments/verify",
        title="G & G Homes Payment",
        description=f"{payload.payment_type.value.replace('_', ' ').title()} payment",
        property_id=payload.property_id,
        tenancy_start_date=payload.tenancy_start_date,
        tenancy_end_date=payload.tenancy_end_date,
    )
    return PaymentLinkResponse(payment=PaymentResponse.model_validate(payment), checkout_url=checkout_url)


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentResponse:
    payment = db.scalar(select(Payment).where(Payment.flutterwave_reference == payload.tx_ref))
    if not payment or payment.payer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    verification = await verify_flutterwave_payment(payload.tx_ref, payload.transaction_id)
    payment.status = PaymentStatus.SUCCESS if verification.get("status") == "successful" else PaymentStatus.FAILED
    payment.flutterwave_transaction_id = str(verification.get("id")) if verification.get("id") else None
    db.commit()
    db.refresh(payment)

    if payment.status == PaymentStatus.SUCCESS:
        create_notification(
            db,
            current_user.id,
            "Payment confirmed",
            f"Your payment {payment.flutterwave_reference} has been confirmed.",
            NotificationType.PAYMENT,
        )
        db.commit()
        await send_email(
            [current_user.email],
            "Payment confirmed",
            f"<p>Your payment reference <strong>{payment.flutterwave_reference}</strong> has been confirmed.</p>",
        )
    return PaymentResponse.model_validate(payment)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def flutterwave_webhook(
    request: Request,
    db: Session = Depends(get_db),
    verif_hash: str = Header(default="", alias="verif-hash"),
) -> dict[str, str]:
    if settings.flutterwave_webhook_secret and verif_hash != settings.flutterwave_webhook_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook secret.")

    payload = await request.json()
    tx_ref = payload.get("data", {}).get("tx_ref")
    if not tx_ref:
        return {"status": "ignored"}

    payment = db.scalar(select(Payment).where(Payment.flutterwave_reference == tx_ref))
    if not payment:
        return {"status": "not-found"}

    payment.status = PaymentStatus.SUCCESS if payload.get("data", {}).get("status") == "successful" else PaymentStatus.FAILED
    payment.flutterwave_transaction_id = str(payload.get("data", {}).get("id", ""))
    payment.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "processed"}
