from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.subscription import Subscription, SubscriptionPlan
from app.models.user import User, UserRole
from app.services.helpers import generate_id


def main() -> None:
    db = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if admin:
            print("Admin already exists.")
            return
        user = User(
            id=generate_id(),
            full_name="G & G Admin",
            email=settings.admin_email.lower(),
            phone_number="+2348078330008",
            password_hash=get_password_hash(settings.admin_password),
            role=UserRole.ADMIN,
            id_verified=True,
        )
        subscription = Subscription(
            id=generate_id(),
            user_id=user.id,
            plan=SubscriptionPlan.STANDARD,
            is_active=True,
        )
        db.add(user)
        db.add(subscription)
        db.commit()
        print("Admin created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
