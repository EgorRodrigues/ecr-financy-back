from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.categories import CategoryCreate, CategoryUpdate, CategoryOut


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_category(session, data: CategoryCreate) -> CategoryOut:
    cid = uuid1()
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_category",
        "INSERT INTO categories (user_id, id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (data.user_id, cid, data.name, data.description, now, now))
    return CategoryOut(user_id=data.user_id, id=cid, name=data.name, description=data.description, created_at=now, updated_at=now)


def list_categories(session, user_id: UUID, limit: int = 50) -> list[CategoryOut]:
    stmt = _prepare(
        session,
        "list_categories",
        "SELECT user_id, id, name, description, created_at, updated_at FROM categories WHERE user_id = ? LIMIT ?",
    )
    rows = session.execute(stmt, (user_id, limit))
    return [
        CategoryOut(
            user_id=row.user_id,
            id=row.id,
            name=row.name,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_category(session, user_id: UUID, cid: UUID) -> CategoryOut | None:
    stmt = _prepare(
        session,
        "get_category",
        "SELECT user_id, id, name, description, created_at, updated_at FROM categories WHERE user_id = ? AND id = ?",
    )
    row = session.execute(stmt, (user_id, cid)).one()
    if not row:
        return None
    return CategoryOut(user_id=row.user_id, id=row.id, name=row.name, description=row.description, created_at=row.created_at, updated_at=row.updated_at)


def update_category(session, user_id: UUID, cid: UUID, data: CategoryUpdate) -> CategoryOut | None:
    current = get_category(session, user_id, cid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    now = datetime.utcnow()
    cql = "UPDATE categories SET name = ?, description = ?, updated_at = ? WHERE user_id = ? AND id = ?"
    stmt = _prepare(session, "update_category", cql)
    session.execute(stmt, (new_name, new_desc, now, user_id, cid))
    return CategoryOut(user_id=user_id, id=cid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now)


def delete_category(session, user_id: UUID, cid: UUID) -> bool:
    stmt = _prepare(session, "delete_category", "DELETE FROM categories WHERE user_id = ? AND id = ?")
    session.execute(stmt, (user_id, cid))
    return True
