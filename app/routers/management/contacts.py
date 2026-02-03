from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.contacts import ContactCreate, ContactOut, ContactUpdate
from app.repositories.contacts import (
    create_contact,
    delete_contact,
    list_contacts,
    update_contact,
)

router = APIRouter()


@router.post("/", response_model=ContactOut)
def create(payload: ContactCreate, session: Session = Depends(get_db)):
    return create_contact(session, payload)


@router.get("/", response_model=list[ContactOut])
def list_(limit: int = 500, session: Session = Depends(get_db)):
    return list_contacts(session, limit)


@router.put("/{contact_id}", response_model=ContactOut)
def update(contact_id: UUID, payload: ContactUpdate, session: Session = Depends(get_db)):
    item = update_contact(session, contact_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Contact not found")
    return item


@router.delete("/{contact_id}")
def delete(contact_id: UUID, session: Session = Depends(get_db)):
    delete_contact(session, contact_id)
    return {"deleted": True}
