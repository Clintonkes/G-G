from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel
from app.schemas.property import PropertyResponse


class SavedPropertyCreate(BaseModel):
    property_id: str


class SavedPropertyResponse(ORMModel):
    id: str
    user_id: str
    property_id: str
    created_at: datetime
    property: PropertyResponse
