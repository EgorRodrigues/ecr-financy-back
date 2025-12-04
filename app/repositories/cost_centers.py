from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.cost_centers import CostCenterCreate, CostCenterUpdate, CostCenterOut


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_cost_center(session, data: CostCenterCreate) -> CostCenterOut:
    ccid = uuid1()
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_cost_center",
        "INSERT INTO cost_centers (id, name, description, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (ccid, data.name, data.description, now, now, data.active))
    return CostCenterOut(id=ccid, name=data.name, description=data.description, created_at=now, updated_at=now, active=data.active)


def list_cost_centers(session, limit: int = 50) -> list[CostCenterOut]:
    stmt = _prepare(
        session,
        "list_cost_centers",
        "SELECT id, name, description, created_at, updated_at, active FROM cost_centers LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
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
    stmt = _prepare(
        session,
        "get_cost_center",
        "SELECT id, name, description, created_at, updated_at, active FROM cost_centers WHERE id = ?",
    )
    row = session.execute(stmt, (ccid,)).one()
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
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_cost_center",
        "UPDATE cost_centers SET name = ?, description = ?, active = ?, updated_at = ? WHERE id = ?",
    )
    session.execute(stmt, (new_name, new_desc, new_active, now, ccid))
    return CostCenterOut(id=ccid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now, active=new_active)


def delete_cost_center(session, ccid: UUID) -> bool:
    stmt = _prepare(session, "delete_cost_center", "DELETE FROM cost_centers WHERE id = ?")
    session.execute(stmt, (ccid,))
    return True
