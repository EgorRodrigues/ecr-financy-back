from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.contacts import ContactCreate, ContactUpdate, ContactOut
from app.repositories.contacts import (
    create_contact,
    list_contacts,
    get_contact,
    update_contact,
    delete_contact,
)


router = APIRouter()


@router.post("/", response_model=ContactOut)
def create(request: Request, payload: ContactCreate):
    session = request.app.state.cassandra_session
    return create_contact(session, payload)


@router.get("/", response_model=list[ContactOut])
def list_(request: Request, limit: int = 50):
    session = request.app.state.cassandra_session
    return list_contacts(session, limit)


@router.get("/{contact_id}", response_model=ContactOut)
def get(request: Request, contact_id: UUID):
    session = request.app.state.cassandra_session
    item = get_contact(session, contact_id)
    if not item:
        raise HTTPException(status_code=404, detail="Contact not found")
    return item


@router.patch("/{contact_id}", response_model=ContactOut)
def update(request: Request, contact_id: UUID, payload: ContactUpdate):
    session = request.app.state.cassandra_session
    item = update_contact(session, contact_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Contact not found")
    return item


@router.delete("/{contact_id}")
def delete(request: Request, contact_id: UUID):
    session = request.app.state.cassandra_session
    delete_contact(session, contact_id)
    return {"deleted": True}

