from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from app.db.postgres import cost_centers
from app.models.cost_centers import CostCenterCreate, CostCenterOut, CostCenterUpdate


def create_cost_center(session: Session, data: CostCenterCreate) -> CostCenterOut:
    stmt = (
        insert(cost_centers)
        .values(
            name=data.name,
            description=data.description,
            active=data.active,
            created_at=func.now(),
            updated_at=func.now(),
        )
        .returning(
            cost_centers.c.id,
            cost_centers.c.name,
            cost_centers.c.description,
            cost_centers.c.created_at,
            cost_centers.c.updated_at,
            cost_centers.c.active,
        )
    )

    result = session.execute(stmt).one()
    session.commit()

    return CostCenterOut(
        id=result.id,
        name=result.name,
        description=result.description,
        created_at=result.created_at,
        updated_at=result.updated_at,
        active=result.active,
    )


def list_cost_centers(session: Session, limit: int) -> list[CostCenterOut]:
    stmt = select(cost_centers).limit(limit)
    result = session.execute(stmt).all()

    return [
        CostCenterOut(
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            active=row.active,
        )
        for row in result
    ]


def get_cost_center(session: Session, cost_center_id: UUID) -> CostCenterOut | None:
    stmt = select(cost_centers).where(cost_centers.c.id == cost_center_id)
    result = session.execute(stmt).one_or_none()

    if not result:
        return None

    return CostCenterOut(
        id=result.id,
        name=result.name,
        description=result.description,
        created_at=result.created_at,
        updated_at=result.updated_at,
        active=result.active,
    )


def update_cost_center(
    session: Session, cost_center_id: UUID, data: CostCenterUpdate
) -> CostCenterOut | None:
    values = data.model_dump(exclude_unset=True)
    if not values:
        return get_cost_center(session, cost_center_id)

    values["updated_at"] = func.now()

    stmt = (
        update(cost_centers)
        .where(cost_centers.c.id == cost_center_id)
        .values(**values)
        .returning(
            cost_centers.c.id,
            cost_centers.c.name,
            cost_centers.c.description,
            cost_centers.c.created_at,
            cost_centers.c.updated_at,
            cost_centers.c.active,
        )
    )

    result = session.execute(stmt).one_or_none()
    session.commit()

    if not result:
        return None

    return CostCenterOut(
        id=result.id,
        name=result.name,
        description=result.description,
        created_at=result.created_at,
        updated_at=result.updated_at,
        active=result.active,
    )


def delete_cost_center(session: Session, cost_center_id: UUID) -> bool:
    stmt = delete(cost_centers).where(cost_centers.c.id == cost_center_id)
    result: Any = session.execute(stmt)
    session.commit()
    return result.rowcount > 0
