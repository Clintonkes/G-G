from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class SavedProperty(Base):
    __tablename__ = "saved_properties"
    __table_args__ = (UniqueConstraint("user_id", "property_id", name="uq_saved_user_property"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="saved_properties")
    property = relationship("Property", back_populates="saved_by")
