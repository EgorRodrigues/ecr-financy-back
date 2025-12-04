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
        "INSERT INTO categories (id, name, description, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (cid, data.name, data.description, now, now, data.active))
    return CategoryOut(id=cid, name=data.name, description=data.description, created_at=now, updated_at=now, active=data.active)


def list_categories(session, limit: int = 50) -> list[CategoryOut]:
    stmt = _prepare(
        session,
        "list_categories",
        "SELECT id, name, description, created_at, updated_at, active FROM categories LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
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
    stmt = _prepare(
        session,
        "get_category",
        "SELECT id, name, description, created_at, updated_at, active FROM categories WHERE id = ?",
    )
    row = session.execute(stmt, (cid,)).one()
    if not row:
        return None
    return CategoryOut(id=row.id, name=row.name, description=row.description, created_at=row.created_at, updated_at=row.updated_at, active=row.active)


def update_category(session, cid: UUID, data: CategoryUpdate) -> CategoryOut | None:
    current = get_category(session, cid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    new_active = data.active if data.active is not None else current.active
    now = datetime.utcnow()
    cql = "UPDATE categories SET name = ?, description = ?, active = ?, updated_at = ? WHERE id = ?"
    stmt = _prepare(session, "update_category", cql)
    session.execute(stmt, (new_name, new_desc, new_active, now, cid))
    return CategoryOut(id=cid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now, active=new_active)


def delete_category(session, cid: UUID) -> bool:
    stmt = _prepare(session, "delete_category", "DELETE FROM categories WHERE id = ?")
    session.execute(stmt, (cid,))
    return True
