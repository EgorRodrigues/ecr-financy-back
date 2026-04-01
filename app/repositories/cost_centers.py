from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cost_centers import CostCenter
from app.schemas.cost_centers import CostCenterCreate, CostCenterOut, CostCenterUpdate


def create_cost_center(session: Session, data: CostCenterCreate) -> CostCenterOut:
    db_cost_center = CostCenter(
        **data.model_dump(),
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_cost_center)
    session.commit()
    return CostCenterOut.model_validate(db_cost_center)


def list_cost_centers(session: Session, limit: int = 50) -> list[CostCenterOut]:
    query = select(CostCenter).order_by(CostCenter.name.asc()).limit(limit)
    rows = session.scalars(query).all()
    return [CostCenterOut.model_validate(row) for row in rows]


def get_cost_center(session: Session, cost_center_id: UUID) -> CostCenterOut | None:
    db_cost_center = session.get(CostCenter, cost_center_id)
    if not db_cost_center:
        return None
    return CostCenterOut.model_validate(db_cost_center)


def update_cost_center(
    session: Session, cost_center_id: UUID, data: CostCenterUpdate
) -> CostCenterOut | None:
    db_cost_center = session.get(CostCenter, cost_center_id)
    if not db_cost_center:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cost_center, key, value)

    db_cost_center.updated_at = datetime.now(UTC)
    session.commit()
    return CostCenterOut.model_validate(db_cost_center)


def delete_cost_center(session: Session, cost_center_id: UUID):
    db_cost_center = session.get(CostCenter, cost_center_id)
    if db_cost_center:
        session.delete(db_cost_center)
        session.commit()
