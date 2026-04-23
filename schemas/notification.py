from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationType
from app.schemas.common import ORMModel


class NotificationResponse(ORMModel):
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime


class NotificationUpdateRequest(BaseModel):
    ids: list[str] = []
    mark_all: bool = False
