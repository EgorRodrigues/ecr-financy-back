from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.subcategories import SubcategoryCreate, SubcategoryUpdate, SubcategoryOut
from app.repositories.subcategories import (
    create_subcategory,
    list_subcategories,
    get_subcategory,
    update_subcategory,
    delete_subcategory,
)


router = APIRouter()


@router.post("/", response_model=SubcategoryOut)
def create(request: Request, payload: SubcategoryCreate):
    session = request.app.state.cassandra_session
    return create_subcategory(session, payload)


@router.get("/{user_id}/{category_id}", response_model=list[SubcategoryOut])
def list_(request: Request, user_id: UUID, category_id: UUID, limit: int = 50):
    session = request.app.state.cassandra_session
    return list_subcategories(session, user_id, category_id, limit)


@router.get("/{user_id}/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def get(request: Request, user_id: UUID, category_id: UUID, subcategory_id: UUID):
    session = request.app.state.cassandra_session
    item = get_subcategory(session, user_id, category_id, subcategory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return item


@router.patch("/{user_id}/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def update(request: Request, user_id: UUID, category_id: UUID, subcategory_id: UUID, payload: SubcategoryUpdate):
    session = request.app.state.cassandra_session
    item = update_subcategory(session, user_id, category_id, subcategory_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return item


@router.delete("/{user_id}/{category_id}/{subcategory_id}")
def delete(request: Request, user_id: UUID, category_id: UUID, subcategory_id: UUID):
    session = request.app.state.cassandra_session
    delete_subcategory(session, user_id, category_id, subcategory_id)
    return {"deleted": True}

