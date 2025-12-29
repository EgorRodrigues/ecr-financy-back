from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import select, insert, update, delete
from app.models.subcategories import (
    SubcategoryCreate,
    SubcategoryUpdate,
    SubcategoryOut,
    SubcategoryMove,
)
from app.db.postgres import subcategories


def create_subcategory(session, data: SubcategoryCreate) -> SubcategoryOut:
    sid = uuid4()
    now = datetime.now(timezone.utc)
    session.execute(
        insert(subcategories).values(
            id=sid,
            category_id=data.category_id,
            name=data.name,
            description=data.description,
            created_at=now,
            updated_at=now,
            active=data.active,
        )
    )
    session.commit()
    return SubcategoryOut(
        category_id=data.category_id,
        id=sid,
        name=data.name,
        description=data.description,
        created_at=now,
        updated_at=now,
        active=data.active,
    )


def list_subcategories(session, category_id: UUID, limit: int = 50) -> list[SubcategoryOut]:
    rows = session.execute(
        select(
            subcategories.c.category_id,
            subcategories.c.id,
            subcategories.c.name,
            subcategories.c.description,
            subcategories.c.created_at,
            subcategories.c.updated_at,
            subcategories.c.active,
        )
        .where(subcategories.c.category_id == category_id)
        .limit(limit)
    ).all()
    return [
        SubcategoryOut(
            category_id=row.category_id,
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in rows
    ]


def list_all_subcategories(session, limit: int = 50) -> list[SubcategoryOut]:
    rows = session.execute(
        select(
            subcategories.c.category_id,
            subcategories.c.id,
            subcategories.c.name,
            subcategories.c.description,
            subcategories.c.created_at,
            subcategories.c.updated_at,
            subcategories.c.active,
        ).limit(limit)
    ).all()
    return [
        SubcategoryOut(
            category_id=row.category_id,
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in rows
    ]


def get_subcategory(session, category_id: UUID, sid: UUID) -> SubcategoryOut | None:
    row = session.execute(
        select(
            subcategories.c.category_id,
            subcategories.c.id,
            subcategories.c.name,
            subcategories.c.description,
            subcategories.c.created_at,
            subcategories.c.updated_at,
            subcategories.c.active,
        ).where((subcategories.c.category_id == category_id) & (subcategories.c.id == sid))
    ).one_or_none()
    if not row:
        return None
    return SubcategoryOut(
        category_id=row.category_id,
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
        updated_at=row.updated_at,
        active=row.active,
    )


def update_subcategory(
    session, category_id: UUID, sid: UUID, data: SubcategoryUpdate
) -> SubcategoryOut | None:
    current = get_subcategory(session, category_id, sid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    new_active = data.active if data.active is not None else current.active
    now = datetime.now(timezone.utc)
    session.execute(
        update(subcategories)
        .where((subcategories.c.category_id == category_id) & (subcategories.c.id == sid))
        .values(name=new_name, description=new_desc, active=new_active, updated_at=now)
    )
    session.commit()
    return SubcategoryOut(
        category_id=category_id,
        id=sid,
        name=new_name,
        description=new_desc,
        created_at=current.created_at,
        updated_at=now,
        active=new_active,
    )


def delete_subcategory(session, category_id: UUID, sid: UUID) -> bool:
    session.execute(
        delete(subcategories).where(
            (subcategories.c.category_id == category_id) & (subcategories.c.id == sid)
        )
    )
    session.commit()
    return True


def move_subcategory(
    session, from_category_id: UUID, sid: UUID, payload: SubcategoryMove
) -> SubcategoryOut | None:
    current = get_subcategory(session, from_category_id, sid)
    if not current:
        return None
    now = datetime.now(timezone.utc)
    session.execute(
        update(subcategories)
        .where(subcategories.c.id == sid)
        .values(category_id=payload.new_category_id, updated_at=now)
    )
    session.commit()
    moved = get_subcategory(session, payload.new_category_id, sid)
    return moved
