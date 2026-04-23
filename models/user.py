import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class UserRole(str, enum.Enum):
    TENANT = "TENANT"
    LANDLORD = "LANDLORD"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.TENANT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    id_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    id_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    properties = relationship("Property", back_populates="landlord", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="tenant", foreign_keys="Appointment.tenant_id")
    landlord_appointments = relationship("Appointment", back_populates="landlord", foreign_keys="Appointment.landlord_id")
    payments = relationship("Payment", back_populates="payer")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_properties = relationship("SavedProperty", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
