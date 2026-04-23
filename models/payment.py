import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PaymentType(str, enum.Enum):
    RENT = "RENT"
    SUBSCRIPTION = "SUBSCRIPTION"
    VERIFICATION = "VERIFICATION"
    PREMIUM_LISTING = "PREMIUM_LISTING"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    property_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("properties.id"), nullable=True, index=True)
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    gross_amount: Mapped[float] = mapped_column(Float, nullable=False)
    platform_fee: Mapped[float] = mapped_column(Float, nullable=False)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)
    flutterwave_reference: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    flutterwave_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    landlord_remitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remittance_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenancy_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tenancy_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    payer = relationship("User", back_populates="payments")
    property = relationship("Property", back_populates="payments")
