from cassandra.query import PreparedStatement
from uuid import UUID, uuid1
from datetime import datetime
from app.models.contacts import ContactCreate, ContactUpdate, ContactOut


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


def create_contact(session, data: ContactCreate) -> ContactOut:
    cid = uuid1()
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "insert_contact",
        "INSERT INTO contacts (id, type, person_type, name, document, email, phone_e164, phone_local, address, notes, active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    )
    session.execute(
        stmt,
        (
            cid,
            data.type,
            data.person_type,
            data.name,
            data.document,
            data.email,
            data.phone_e164,
            data.phone_local,
            data.address,
            data.notes,
            data.active,
            now,
            now,
        ),
    )
    return ContactOut(
        id=cid,
        type=data.type,
        person_type=data.person_type, 
        name=data.name,
        document=data.document,
        email=data.email,
        phone_e164=data.phone_e164,
        phone_local=data.phone_local,
        address=data.address,
        notes=data.notes,
        active=data.active,
        created_at=now,
        updated_at=now,
    )


def list_contacts(session, limit: int = 50) -> list[ContactOut]:
    stmt = _prepare(
        session,
        "list_contacts",
        "SELECT id, type, person_type, name, document, email, phone_e164, phone_local, address, notes, active, created_at, updated_at FROM contacts LIMIT ?",
    )
    rows = session.execute(stmt, (limit,))
    return [
        ContactOut(
            id=row.id,
            type=row.type,
            person_type=row.person_type,
            name=row.name,
            document=row.document,
            email=row.email,
            phone_e164=row.phone_e164,
            phone_local=row.phone_local,
            address=row.address,
            notes=row.notes,
            active=row.active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_contact(session, cid: UUID) -> ContactOut | None:
    stmt = _prepare(
        session,
        "get_contact",
        "SELECT id, type, person_type, name, document, email, phone_e164, phone_local, address, notes, active, created_at, updated_at FROM contacts WHERE id = ?",
    )
    row = session.execute(stmt, (cid,)).one()
    if not row:
        return None
    return ContactOut(
        id=row.id,
        type=row.type,
        person_type=row.person_type,
        name=row.name,
        document=row.document,
        email=row.email,
        phone_e164=row.phone_e164,
        phone_local=row.phone_local,
        address=row.address,
        notes=row.notes,
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_contact(session, cid: UUID, data: ContactUpdate) -> ContactOut | None:
    current = get_contact(session, cid)
    if not current:
        return None
    new_type = data.type if data.type is not None else current.type
    new_person_type = data.person_type if data.person_type is not None else current.person_type
    new_name = data.name if data.name is not None else current.name
    new_document = data.document if data.document is not None else current.document
    new_email = data.email if data.email is not None else current.email
    new_phone_e164 = data.phone_e164 if data.phone_e164 is not None else current.phone_e164
    new_phone_local = data.phone_local if data.phone_local is not None else current.phone_local
    new_address = data.address if data.address is not None else current.address
    new_notes = data.notes if data.notes is not None else current.notes
    new_active = data.active if data.active is not None else current.active
    now = datetime.utcnow()
    stmt = _prepare(
        session,
        "update_contact",
        "UPDATE contacts SET type = ?, person_type = ?, name = ?, document = ?, email = ?, phone_e164 = ?, phone_local = ?, address = ?, notes = ?, active = ?, updated_at = ? WHERE id = ?",
    )
    session.execute(
        stmt,
        (
            new_type,
            new_person_type,
            new_name,
            new_document,
            new_email,
            new_phone_e164,
            new_phone_local,
            new_address,
            new_notes,
            new_active,
            now,
            cid,
        ),
    )
    return ContactOut(
        id=cid,
        type=new_type,
        person_type=new_person_type,
        name=new_name,
        document=new_document,
        email=new_email,
        phone_e164=new_phone_e164,
        phone_local=new_phone_local,
        address=new_address,
        notes=new_notes,
        active=new_active,
        created_at=current.created_at,
        updated_at=now,
    )


def delete_contact(session, cid: UUID) -> bool:
    stmt = _prepare(session, "delete_contact", "DELETE FROM contacts WHERE id = ?")
    session.execute(stmt, (cid,))
    return True
