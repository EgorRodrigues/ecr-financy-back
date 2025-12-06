from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.subcategories import SubcategoryCreate, SubcategoryUpdate, SubcategoryOut, SubcategoryMove


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
        "INSERT INTO subcategories (category_id, id, name, description, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
    )
    session.execute(stmt, (data.category_id, sid, data.name, data.description, now, now, data.active))
    return SubcategoryOut(category_id=data.category_id, id=sid, name=data.name, description=data.description, created_at=now, updated_at=now, active=data.active)


def list_subcategories(session, category_id: UUID, limit: int = 50) -> list[SubcategoryOut]:
    stmt = _prepare(
        session,
        "list_subcategories",
        "SELECT category_id, id, name, description, created_at, updated_at, active FROM subcategories WHERE category_id = ? LIMIT ?",
    )
    rows = session.execute(stmt, (category_id, limit))
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
    stmt = _prepare(
        session,
        "list_all_subcategories",
        "SELECT category_id, id, name, description, created_at, updated_at, active FROM subcategories LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
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
    stmt = _prepare(
        session,
        "get_subcategory",
        "SELECT category_id, id, name, description, created_at, updated_at, active FROM subcategories WHERE category_id = ? AND id = ?",
    )
    row = session.execute(stmt, (category_id, sid)).one()
    if not row:
        return None
    return SubcategoryOut(category_id=row.category_id, id=row.id, name=row.name, description=row.description, created_at=row.created_at, updated_at=row.updated_at, active=row.active)


def update_subcategory(session, category_id: UUID, sid: UUID, data: SubcategoryUpdate) -> SubcategoryOut | None:
    current = get_subcategory(session, category_id, sid)
    if not current:
        return None
    new_name = data.name if data.name is not None else current.name
    new_desc = data.description if data.description is not None else current.description
    new_active = data.active if data.active is not None else current.active
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_subcategory",
        "UPDATE subcategories SET name = ?, description = ?, active = ?, updated_at = ? WHERE category_id = ? AND id = ?",
    )
    session.execute(stmt, (new_name, new_desc, new_active, now, category_id, sid))
    return SubcategoryOut(category_id=category_id, id=sid, name=new_name, description=new_desc, created_at=current.created_at, updated_at=now, active=new_active)


def delete_subcategory(session, category_id: UUID, sid: UUID) -> bool:
    stmt = _prepare(session, "delete_subcategory", "DELETE FROM subcategories WHERE category_id = ? AND id = ?")
    session.execute(stmt, (category_id, sid))
    return True


def move_subcategory(session, from_category_id: UUID, sid: UUID, payload: SubcategoryMove) -> SubcategoryOut | None:
    current = get_subcategory(session, from_category_id, sid)
    if not current:
        return None
    now = datetime.utcnow()
    stmt_insert = _prepare(
        session,
        "insert_subcategory",
        "INSERT INTO subcategories (category_id, id, name, description, created_at, updated_at, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
    )
    session.execute(
        stmt_insert,
        (
            payload.new_category_id,
            sid,
            current.name,
            current.description,
            current.created_at,
            now,
            current.active,
        ),
    )
    delete_subcategory(session, from_category_id, sid)
    return SubcategoryOut(
        category_id=payload.new_category_id,
        id=sid,
        name=current.name,
        description=current.description,
        created_at=current.created_at,
        updated_at=now,
        active=current.active,
    )
