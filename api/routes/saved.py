from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from db.session import get_db
from models.property import Property, PropertyStatus
from models.saved_property import SavedProperty
from models.user import User
from schemas.saved import SavedPropertyCreate, SavedPropertyResponse
from services.dependencies import get_current_user
from services.helpers import generate_id


router = APIRouter()


@router.get("", response_model=list[SavedPropertyResponse])
def list_saved_properties(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[SavedPropertyResponse]:
    items = db.scalars(
        select(SavedProperty).options(joinedload(SavedProperty.property)).where(SavedProperty.user_id == current_user.id)
    ).all()
    return [SavedPropertyResponse.model_validate(item) for item in items]


@router.post("", response_model=SavedPropertyResponse, status_code=status.HTTP_201_CREATED)
def save_property(
    payload: SavedPropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedPropertyResponse:
    property_record = db.get(Property, payload.property_id)
    if not property_record or property_record.status != PropertyStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Property not found.")
    existing = db.scalar(select(SavedProperty).where(SavedProperty.user_id == current_user.id, SavedProperty.property_id == payload.property_id))
    if existing:
        return SavedPropertyResponse.model_validate(existing)
    saved = SavedProperty(id=generate_id(), user_id=current_user.id, property_id=payload.property_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return SavedPropertyResponse.model_validate(saved)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_property(property_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    saved = db.scalar(select(SavedProperty).where(SavedProperty.user_id == current_user.id, SavedProperty.property_id == property_id))
    if not saved:
        raise HTTPException(status_code=404, detail="Saved property not found.")
    db.delete(saved)
    db.commit()
