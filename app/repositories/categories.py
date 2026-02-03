from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.categories import Category
from app.schemas.categories import CategoryCreate, CategoryOut, CategoryUpdate


def create_category(session: Session, data: CategoryCreate) -> CategoryOut:
    db_category = Category(
        **data.model_dump(),
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return CategoryOut.model_validate(db_category)


def list_categories(session: Session, limit: int = 50) -> list[CategoryOut]:
    query = select(Category).order_by(Category.name.asc()).limit(limit)
    rows = session.scalars(query).all()
    return [CategoryOut.model_validate(row) for row in rows]


def get_category(session: Session, cid: UUID) -> CategoryOut | None:
    db_category = session.get(Category, cid)
    if not db_category:
        return None
    return CategoryOut.model_validate(db_category)


def update_category(session: Session, cid: UUID, data: CategoryUpdate) -> CategoryOut | None:
    db_category = session.get(Category, cid)
    if not db_category:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db_category.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(db_category)
    return CategoryOut.model_validate(db_category)


def delete_category(session: Session, cid: UUID):
    db_category = session.get(Category, cid)
    if db_category:
        session.delete(db_category)
        session.commit()
