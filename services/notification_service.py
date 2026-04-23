from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.services.helpers import generate_id


def create_notification(db: Session, user_id: str, title: str, message: str, type_: NotificationType) -> Notification:
    notification = Notification(
        id=generate_id(),
        user_id=user_id,
        title=title,
        message=message,
        type=type_,
    )
    db.add(notification)
    db.flush()
    return notification
