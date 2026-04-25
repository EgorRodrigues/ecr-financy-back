from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contacts import Contact
from app.schemas.contacts import ContactCreate, ContactOut, ContactUpdate


def create_contact(session: Session, data: ContactCreate) -> ContactOut:
    db_contact = Contact(
        **data.model_dump(),
        id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(db_contact)
    session.commit()
    return ContactOut.model_validate(db_contact)


def list_contacts(session: Session, limit: int = 50) -> list[ContactOut]:
    query = select(Contact).order_by(Contact.name.asc()).limit(limit)
    rows = session.scalars(query).all()
    return [ContactOut.model_validate(row) for row in rows]


def get_contact(session: Session, cid: UUID) -> ContactOut | None:
    db_contact = session.get(Contact, cid)
    if not db_contact:
        return None
    return ContactOut.model_validate(db_contact)


def update_contact(session: Session, cid: UUID, data: ContactUpdate) -> ContactOut | None:
    db_contact = session.get(Contact, cid)
    if not db_contact:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_contact, key, value)

    db_contact.updated_at = datetime.now(UTC)
    session.commit()
    return ContactOut.model_validate(db_contact)


def delete_contact(session: Session, cid: UUID):
    db_contact = session.get(Contact, cid)
    if db_contact:
        session.delete(db_contact)
        session.commit()
