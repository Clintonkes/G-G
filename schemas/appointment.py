from datetime import datetime

from pydantic import BaseModel, Field

from app.models.appointment import AppointmentOutcome, AppointmentStatus
from app.schemas.common import ORMModel


class AppointmentCreate(BaseModel):
    property_id: str
    scheduled_date: datetime
    tenant_notes: str | None = Field(default=None, max_length=1000)


class AppointmentUpdate(BaseModel):
    scheduled_date: datetime | None = None
    status: AppointmentStatus | None = None
    outcome: AppointmentOutcome | None = None
    admin_notes: str | None = None


class AppointmentResponse(ORMModel):
    id: str
    tenant_id: str
    property_id: str
    landlord_id: str
    scheduled_date: datetime
    status: AppointmentStatus
    outcome: AppointmentOutcome
    tenant_notes: str | None
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime
