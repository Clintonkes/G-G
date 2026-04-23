from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from models.notification import Notification
from models.user import User
from schemas.notification import NotificationResponse, NotificationUpdateRequest
from services.dependencies import get_current_user


router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[NotificationResponse]:
    items = db.scalars(
        select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    ).all()
    return [NotificationResponse.model_validate(item) for item in items]


@router.patch("", response_model=list[NotificationResponse])
def mark_notifications(
    payload: NotificationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationResponse]:
    query = select(Notification).where(Notification.user_id == current_user.id)
    if not payload.mark_all and payload.ids:
        query = query.where(Notification.id.in_(payload.ids))
    items = db.scalars(query).all()
    for item in items:
        item.is_read = True
    db.commit()
    return [NotificationResponse.model_validate(item) for item in items]
