from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import select, insert, update, delete
from app.models.cost_centers import CostCenterCreate, CostCenterUpdate, CostCenterOut
from app.db.postgres import cost_centers


def create_cost_center(session, data: CostCenterCreate) -> CostCenterOut:
    ccid = uuid4()
    now = datetime.now(timezone.utc)
    session.execute(
        insert(cost_centers).values(
            id=ccid, name=data.name, description=data.description, created_at=now, updated_at=now, active=data.active
        )
    )
    session.commit()
    return CostCenterOut(id=ccid, name=data.name, description=data.description, created_at=now, updated_at=now, active=data.active)


def list_cost_centers(session, limit: int = 50) -> list[CostCenterOut]:
    rows = session.execute(
        select(
            cost_centers.c.id,
            cost_centers.c.name,
            cost_centers.c.description,
            cost_centers.c.created_at,
            cost_centers.c.updated_at,
            cost_centers.c.active,
        ).limit(limit)
    ).all()
    return [
        CostCenterOut(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in rows
    ]


def get_cost_center(session, ccid: UUID) -> CostCenterOut | None:
    row = session.execute(
        select(
            cost_centers.c.id,
            cost_centers.c.name,
            cost_centers.c.description,
            cost_centers.c.created_at,
            cost_centers.c.updated_at,
            cost_centers.c.active,
        ).where(cost_centers.c.id == ccid)
    ).one_or_none()
    if not row:
        return None
    return CostCenterOut(id=row.id, name=row.name, description=row.description, created_at=row.created_at, updated_at=row.updated_at, active=row.active)


def update_cost_center(session, ccid: UUID, data: CostCenterUpdate) -> CostCenterOut | None:
    current = get_cost_center(session, ccid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    new_active = data.active if data.active is not None else current.active
    now = datetime.now(timezone.utc)
    session.execute(
        update(cost_centers)
        .where(cost_centers.c.id == ccid)
        .values(name=new_name, description=new_desc, active=new_active, updated_at=now)
    )
    session.commit()
    return CostCenterOut(id=ccid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now, active=new_active)


def delete_cost_center(session, ccid: UUID) -> bool:
    session.execute(delete(cost_centers).where(cost_centers.c.id == ccid))
    session.commit()
    return True
