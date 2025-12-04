from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.subcategories import SubcategoryCreate, SubcategoryUpdate, SubcategoryOut


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_subcategory(session, data: SubcategoryCreate) -> SubcategoryOut:
    sid = uuid1()
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_subcategory",
        "INSERT INTO subcategories (user_id, category_id, id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (data.user_id, data.category_id, sid, data.name, data.description, now, now))
    return SubcategoryOut(user_id=data.user_id, category_id=data.category_id, id=sid, name=data.name, description=data.description, created_at=now, updated_at=now)


def list_subcategories(session, user_id: UUID, category_id: UUID, limit: int = 50) -> list[SubcategoryOut]:
    stmt = _prepare(
        session,
        "list_subcategories",
        "SELECT user_id, category_id, id, name, description, created_at, updated_at FROM subcategories WHERE user_id = ? AND category_id = ? LIMIT ?",
    )
    rows = session.execute(stmt, (user_id, category_id, limit))
    return [
        SubcategoryOut(
            user_id=row.user_id,
            category_id=row.category_id,
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_subcategory(session, user_id: UUID, category_id: UUID, sid: UUID) -> SubcategoryOut | None:
    stmt = _prepare(
        session,
        "get_subcategory",
        "SELECT user_id, category_id, id, name, description, created_at, updated_at FROM subcategories WHERE user_id = ? AND category_id = ? AND id = ?",
    )
    row = session.execute(stmt, (user_id, category_id, sid)).one()
    if not row:
        return None
    return SubcategoryOut(user_id=row.user_id, category_id=row.category_id, id=row.id, name=row.name, description=row.description, created_at=row.created_at, updated_at=row.updated_at)


def update_subcategory(session, user_id: UUID, category_id: UUID, sid: UUID, data: SubcategoryUpdate) -> SubcategoryOut | None:
    current = get_subcategory(session, user_id, category_id, sid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_subcategory",
        "UPDATE subcategories SET name = ?, description = ?, updated_at = ? WHERE user_id = ? AND category_id = ? AND id = ?",
    )
    session.execute(stmt, (new_name, new_desc, now, user_id, category_id, sid))
    return SubcategoryOut(user_id=user_id, category_id=category_id, id=sid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now)


def delete_subcategory(session, user_id: UUID, category_id: UUID, sid: UUID) -> bool:
    stmt = _prepare(session, "delete_subcategory", "DELETE FROM subcategories WHERE user_id = ? AND category_id = ? AND id = ?")
    session.execute(stmt, (user_id, category_id, sid))
    return True

