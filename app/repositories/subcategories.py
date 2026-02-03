from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subcategories import Subcategory
from app.schemas.subcategories import SubcategoryCreate, SubcategoryOut, SubcategoryUpdate


def create_subcategory(session: Session, data: SubcategoryCreate) -> SubcategoryOut:
    db_subcategory = Subcategory(
        **data.model_dump(),
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_subcategory)
    session.commit()
    session.refresh(db_subcategory)
    return SubcategoryOut.model_validate(db_subcategory)


def list_subcategories(session: Session, category_id: UUID, limit: int = 50) -> list[SubcategoryOut]:
    query = (
        select(Subcategory)
        .where(Subcategory.category_id == category_id)
        .order_by(Subcategory.name.asc())
        .limit(limit)
    )
    rows = session.scalars(query).all()
    return [SubcategoryOut.model_validate(row) for row in rows]


def list_all_subcategories(session: Session, limit: int = 50) -> list[SubcategoryOut]:
    query = select(Subcategory).order_by(Subcategory.name.asc()).limit(limit)
    rows = session.scalars(query).all()
    return [SubcategoryOut.model_validate(row) for row in rows]


def get_subcategory(session: Session, category_id: UUID, sid: UUID) -> SubcategoryOut | None:
    db_subcategory = session.get(Subcategory, sid)
    if not db_subcategory or db_subcategory.category_id != category_id:
        return None
    return SubcategoryOut.model_validate(db_subcategory)


def update_subcategory(
    session: Session, category_id: UUID, sid: UUID, data: SubcategoryUpdate
) -> SubcategoryOut | None:
    db_subcategory = session.get(Subcategory, sid)
    if not db_subcategory or db_subcategory.category_id != category_id:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subcategory, key, value)

    db_subcategory.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(db_subcategory)
    return SubcategoryOut.model_validate(db_subcategory)


def delete_subcategory(session: Session, category_id: UUID, sid: UUID):
    db_subcategory = session.get(Subcategory, sid)
    if db_subcategory and db_subcategory.category_id == category_id:
        session.delete(db_subcategory)
        session.commit()
