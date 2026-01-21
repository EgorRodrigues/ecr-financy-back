from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, update

from app.db.postgres import contacts
from app.models.contacts import ContactCreate, ContactOut, ContactUpdate


def create_contact(session, data: ContactCreate) -> ContactOut:
    cid = uuid4()
    now = datetime.now(UTC)
    session.execute(
        insert(contacts).values(
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
    )
    session.commit()
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


def list_contacts(session, limit: int) -> list[ContactOut]:
    rows = session.execute(
        select(
            contacts.c.id,
            contacts.c.type,
            contacts.c.person_type,
            contacts.c.name,
            contacts.c.document,
            contacts.c.email,
            contacts.c.phone_e164,
            contacts.c.phone_local,
            contacts.c.address,
            contacts.c.notes,
            contacts.c.active,
            contacts.c.created_at,
            contacts.c.updated_at,
        ).limit(limit)
    ).all()
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
    row = session.execute(
        select(
            contacts.c.id,
            contacts.c.type,
            contacts.c.person_type,
            contacts.c.name,
            contacts.c.document,
            contacts.c.email,
            contacts.c.phone_e164,
            contacts.c.phone_local,
            contacts.c.address,
            contacts.c.notes,
            contacts.c.active,
            contacts.c.created_at,
            contacts.c.updated_at,
        ).where(contacts.c.id == cid)
    ).one_or_none()
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
    now = datetime.now(UTC)
    session.execute(
        update(contacts)
        .where(contacts.c.id == cid)
        .values(
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
            updated_at=now,
        )
    )
    session.commit()
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
    session.execute(delete(contacts).where(contacts.c.id == cid))
    session.commit()
    return True
