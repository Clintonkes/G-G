import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class PropertyType(str, enum.Enum):
    SELF_CONTAIN = "SELF_CONTAIN"
    FLAT = "FLAT"
    DUPLEX = "DUPLEX"
    BUNGALOW = "BUNGALOW"
    OFFICE_SPACE = "OFFICE_SPACE"
    WAREHOUSE = "WAREHOUSE"


class PropertyStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    ACTIVE = "ACTIVE"
    RENTED = "RENTED"
    INACTIVE = "INACTIVE"


class ListingType(str, enum.Enum):
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    GOLD = "GOLD"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    landlord_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    neighbourhood: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(120), nullable=False, default="Ebonyi State")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    toilets: Mapped[int] = mapped_column(Integer, nullable=False)
    is_furnished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    annual_rent: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="NGN")
    security_deposit: Mapped[float | None] = mapped_column(Float, nullable=True)
    amenities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    has_water: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_electricity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_security: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_parking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    photo_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    video_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    document_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), default=PropertyStatus.DRAFT, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_fully_occupied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    site_visited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    listing_type: Mapped[ListingType] = mapped_column(Enum(ListingType), default=ListingType.STANDARD, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    landlord = relationship("User", back_populates="properties")
    appointments = relationship("Appointment", back_populates="property", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="property")
    saved_by = relationship("SavedProperty", back_populates="property", cascade="all, delete-orphan")
