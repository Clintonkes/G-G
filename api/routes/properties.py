from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, status

from db.session import get_db
from models.property import Property, PropertyStatus, PropertyType
from models.user import User, UserRole
from schemas.property import PropertyCreate, PropertyListResponse, PropertyResponse, PropertyUpdate
from services.ai_service import generate_listing_summary
from services.dependencies import get_current_user, get_optional_current_user
from services.helpers import generate_id


router = APIRouter()


def normalize_property_type(value: str) -> PropertyType:
    normalized = value.strip().upper().replace(" ", "_").replace("-", "_")
    try:
        return PropertyType(normalized)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in PropertyType)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid property_type '{value}'. Use one of: {allowed}.",
        ) from exc


@router.get("", response_model=PropertyListResponse)
async def list_properties(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    q: str | None = None,
    city: str | None = None,
    neighbourhood: str | None = None,
    property_type: str | None = None,
    min_budget: float | None = None,
    max_budget: float | None = None,
    bedrooms: int | None = None,
    verified_only: bool = False,
    include_mine: bool = False,
    current_user: User | None = Depends(get_optional_current_user),
) -> PropertyListResponse:
    query = select(Property)
    count_query = select(func.count(Property.id))

    if include_mine and current_user:
        query = query.where(Property.landlord_id == current_user.id)
        count_query = count_query.where(Property.landlord_id == current_user.id)
    else:
        query = query.where(Property.status == PropertyStatus.ACTIVE)
        count_query = count_query.where(Property.status == PropertyStatus.ACTIVE)

    if q:
        matcher = f"%{q.strip()}%"
        criterion = or_(Property.title.ilike(matcher), Property.address.ilike(matcher), Property.neighbourhood.ilike(matcher))
        query = query.where(criterion)
        count_query = count_query.where(criterion)
    if city:
        normalized_city = city.strip()
        query = query.where(Property.city.ilike(normalized_city))
        count_query = count_query.where(Property.city.ilike(normalized_city))
    if neighbourhood:
        normalized_neighbourhood = neighbourhood.strip()
        query = query.where(Property.neighbourhood.ilike(f"%{normalized_neighbourhood}%"))
        count_query = count_query.where(Property.neighbourhood.ilike(f"%{normalized_neighbourhood}%"))
    if property_type:
        normalized_property_type = normalize_property_type(property_type)
        query = query.where(Property.property_type == normalized_property_type)
        count_query = count_query.where(Property.property_type == normalized_property_type)
    if min_budget is not None:
        query = query.where(Property.annual_rent >= min_budget)
        count_query = count_query.where(Property.annual_rent >= min_budget)
    if max_budget is not None:
        query = query.where(Property.annual_rent <= max_budget)
        count_query = count_query.where(Property.annual_rent <= max_budget)
    if bedrooms is not None:
        query = query.where(Property.bedrooms >= bedrooms if bedrooms >= 4 else Property.bedrooms == bedrooms)
        count_query = count_query.where(Property.bedrooms >= bedrooms if bedrooms >= 4 else Property.bedrooms == bedrooms)
    if verified_only:
        query = query.where(Property.is_verified.is_(True))
        count_query = count_query.where(Property.is_verified.is_(True))

    total = db.scalar(count_query) or 0
    items = db.scalars(
        query.order_by(Property.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return PropertyListResponse(
        items=[PropertyResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    payload: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    if current_user.role not in {UserRole.LANDLORD, UserRole.ADMIN}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Upgrade your account to landlord to list properties.")

    description = await generate_listing_summary(payload.title, payload.description, payload.amenities)
    property_record = Property(
        id=generate_id(),
        landlord_id=current_user.id,
        **payload.model_dump(exclude={"description"}),
        description=description,
    )
    if not property_record.thumbnail_url and property_record.photo_urls:
        property_record.thumbnail_url = property_record.photo_urls[0]
    db.add(property_record)
    db.commit()
    db.refresh(property_record)
    return PropertyResponse.model_validate(property_record)


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(property_id: str, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_current_user)) -> PropertyResponse:
    property_record = db.get(Property, property_id)
    if not property_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")

    if property_record.status != PropertyStatus.ACTIVE and (
        not current_user or (current_user.id != property_record.landlord_id and current_user.role != UserRole.ADMIN)
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    return PropertyResponse.model_validate(property_record)


@router.patch("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: str,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PropertyResponse:
    property_record = db.get(Property, property_id)
    if not property_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    if current_user.role != UserRole.ADMIN and property_record.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot edit this property.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(property_record, field, value)
    db.commit()
    db.refresh(property_record)
    return PropertyResponse.model_validate(property_record)


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    property_record = db.get(Property, property_id)
    if not property_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found.")
    if current_user.role != UserRole.ADMIN and property_record.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot delete this property.")
    db.delete(property_record)
    db.commit()
