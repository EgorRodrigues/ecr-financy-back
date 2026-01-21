from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update

from app.db.postgres import categories
from app.models.categories import CategoryCreate, CategoryOut, CategoryUpdate


def create_category(session, data: CategoryCreate) -> CategoryOut:
    cid = uuid4()
    now = datetime.now(UTC)
    session.execute(
        insert(categories).values(
            id=cid,
            name=data.name,
            description=data.description,
            created_at=now,
            updated_at=now,
            active=data.active,
        )
    )
    session.commit()
    return CategoryOut(
        id=cid,
        name=data.name,
        description=data.description,
        created_at=now,
        updated_at=now,
        active=data.active,
    )


def list_categories(session, limit: int) -> list[CategoryOut]:
    rows = session.execute(
        select(
            categories.c.id,
            categories.c.name,
            categories.c.description,
            categories.c.created_at,
            categories.c.updated_at,
            categories.c.active,
        ).limit(limit)
    ).all()
    return [
        CategoryOut(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in rows
    ]


def get_category(session, cid: UUID) -> CategoryOut | None:
    row = session.execute(
        select(
            categories.c.id,
            categories.c.name,
            categories.c.description,
            categories.c.created_at,
            categories.c.updated_at,
            categories.c.active,
        ).where(categories.c.id == cid)
    ).one_or_none()
    if not row:
        return None
    return CategoryOut(
        id=row.id,
        name=row.name,
        description=row.description,
        created_at=row.created_at,
        updated_at=row.updated_at,
        active=row.active,
    )


def update_category(session, cid: UUID, data: CategoryUpdate) -> CategoryOut | None:
    current = get_category(session, cid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    new_active = data.active if data.active is not None else current.active
    now = datetime.now(UTC)
    session.execute(
        update(categories)
        .where(categories.c.id == cid)
        .values(name=new_name, description=new_desc, active=new_active, updated_at=now)
    )
    session.commit()
    return CategoryOut(
        id=cid,
        name=new_name,
        description=new_desc,
        created_at=current.created_at,
        updated_at=now,
        active=new_active,
    )


def delete_category(session, cid: UUID) -> bool:
    session.execute(delete(categories).where(categories.c.id == cid))
    session.commit()
    return True
