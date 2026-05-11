from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from models.property import ListingType, PropertyStatus, PropertyType
from schemas.common import ORMModel


class PropertyBase(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    description: str = Field(min_length=20)
    address: str
    neighbourhood: str
    city: str
    state: str = "Ebonyi State"
    latitude: float | None = None
    longitude: float | None = None
    property_type: PropertyType
    bedrooms: int = Field(ge=0)
    bathrooms: int = Field(ge=0)
    toilets: int = Field(ge=0)
    is_furnished: bool = False
    annual_rent: float = Field(gt=0)
    currency: str = Field(default="NGN", min_length=3, max_length=8)
    security_deposit: float | None = Field(default=None, ge=0)
    amenities: list[str] = Field(default_factory=list)
    has_water: bool = False
    has_electricity: bool = False
    has_security: bool = False
    has_parking: bool = False
    photo_urls: list[str] = Field(default_factory=list)
    video_urls: list[str] = Field(default_factory=list)
    document_urls: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    listing_type: ListingType = ListingType.STANDARD

    @field_validator("photo_urls")
    @classmethod
    def validate_photos(cls, value: list[str]) -> list[str]:
        if len(value) < 3:
            raise ValueError("At least 3 property photos are required.")
        return value

    @field_validator("document_urls")
    @classmethod
    def validate_documents(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("Ownership documents are required.")
        return value


class PropertyCreate(PropertyBase):
    status: PropertyStatus = PropertyStatus.PENDING_VERIFICATION


class PropertyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    neighbourhood: str | None = None
    city: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    property_type: PropertyType | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    toilets: int | None = Field(default=None, ge=0)
    is_furnished: bool | None = None
    annual_rent: float | None = Field(default=None, gt=0)
    security_deposit: float | None = Field(default=None, ge=0)
    amenities: list[str] | None = None
    has_water: bool | None = None
    has_electricity: bool | None = None
    has_security: bool | None = None
    has_parking: bool | None = None
    photo_urls: list[str] | None = None
    video_urls: list[str] | None = None
    document_urls: list[str] | None = None
    thumbnail_url: str | None = None
    status: PropertyStatus | None = None
    listing_type: ListingType | None = None
    is_fully_occupied: bool | None = None
    site_visited: bool | None = None


class PropertyResponse(ORMModel):
    id: str
    landlord_id: str
    title: str
    description: str
    address: str
    neighbourhood: str
    city: str
    state: str
    latitude: float | None
    longitude: float | None
    property_type: PropertyType
    bedrooms: int
    bathrooms: int
    toilets: int
    is_furnished: bool
    annual_rent: float
    currency: str
    security_deposit: float | None
    amenities: list[str]
    has_water: bool
    has_electricity: bool
    has_security: bool
    has_parking: bool
    photo_urls: list[str]
    video_urls: list[str]
    document_urls: list[str]
    thumbnail_url: str | None
    status: PropertyStatus
    is_verified: bool
    verified_at: datetime | None
    listing_type: ListingType
    is_fully_occupied: bool
    created_at: datetime
    updated_at: datetime


class PropertyListResponse(BaseModel):
    items: list[PropertyResponse]
    total: int
    page: int
    page_size: int
