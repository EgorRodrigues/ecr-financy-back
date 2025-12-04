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
        "INSERT INTO cost_centers (user_id, id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (data.user_id, ccid, data.name, data.description, now, now))
    return CostCenterOut(user_id=data.user_id, id=ccid, name=data.name, description=data.description, created_at=now, updated_at=now)


def list_cost_centers(session, user_id: UUID, limit: int = 50) -> list[CostCenterOut]:
    stmt = _prepare(
        session,
        "list_cost_centers",
        "SELECT user_id, id, name, description, created_at, updated_at FROM cost_centers WHERE user_id = ? LIMIT ?",
    )
    rows = session.execute(stmt, (user_id, limit))
    return [
        CostCenterOut(
            user_id=row.user_id,
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_cost_center(session, user_id: UUID, ccid: UUID) -> CostCenterOut | None:
    stmt = _prepare(
        session,
        "get_cost_center",
        "SELECT user_id, id, name, description, created_at, updated_at FROM cost_centers WHERE user_id = ? AND id = ?",
    )
    row = session.execute(stmt, (user_id, ccid)).one()
    if not row:
        return None
    return CostCenterOut(user_id=row.user_id, id=row.id, name=row.name, description=row.description, created_at=row.created_at, updated_at=row.updated_at)


def update_cost_center(session, user_id: UUID, ccid: UUID, data: CostCenterUpdate) -> CostCenterOut | None:
    current = get_cost_center(session, user_id, ccid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_cost_center",
        "UPDATE cost_centers SET name = ?, description = ?, updated_at = ? WHERE user_id = ? AND id = ?",
    )
    session.execute(stmt, (new_name, new_desc, now, user_id, ccid))
    return CostCenterOut(user_id=user_id, id=ccid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now)


def delete_cost_center(session, user_id: UUID, ccid: UUID) -> bool:
    stmt = _prepare(session, "delete_cost_center", "DELETE FROM cost_centers WHERE user_id = ? AND id = ?")
    session.execute(stmt, (user_id, ccid))
    return True

