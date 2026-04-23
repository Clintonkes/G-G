from datetime import date, datetime

from pydantic import BaseModel, Field

from models.payment import PaymentStatus, PaymentType
from schemas.common import ORMModel


class PaymentInitializeRequest(BaseModel):
    property_id: str | None = None
    payment_type: PaymentType
    gross_amount: float = Field(gt=0)
    tenancy_start_date: date | None = None
    tenancy_end_date: date | None = None


class PaymentVerifyRequest(BaseModel):
    transaction_id: str | None = None
    tx_ref: str


class PaymentResponse(ORMModel):
    id: str
    payer_id: str
    property_id: str | None
    payment_type: PaymentType
    gross_amount: float
    platform_fee: float
    net_amount: float
    flutterwave_reference: str
    flutterwave_transaction_id: str | None
    status: PaymentStatus
    landlord_remitted: bool
    remitted_at: datetime | None
    remittance_reference: str | None
    tenancy_start_date: date | None
    tenancy_end_date: date | None
    created_at: datetime
    updated_at: datetime


class PaymentLinkResponse(BaseModel):
    payment: PaymentResponse
    checkout_url: str
