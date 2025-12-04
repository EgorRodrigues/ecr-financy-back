from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.categories import CategoryCreate, CategoryUpdate, CategoryOut
from app.repositories.categories import (
    create_category,
    list_categories,
    get_category,
    update_category,
    delete_category,
)


router = APIRouter()


@router.post("/", response_model=CategoryOut)
def create(request: Request, payload: CategoryCreate):
    session = request.app.state.cassandra_session
    return create_category(session, payload)


@router.get("/{user_id}", response_model=list[CategoryOut])
def list_(request: Request, user_id: UUID, limit: int = 50):
    session = request.app.state.cassandra_session
    return list_categories(session, user_id, limit)


@router.get("/{user_id}/{category_id}", response_model=CategoryOut)
def get(request: Request, user_id: UUID, category_id: UUID):
    session = request.app.state.cassandra_session
    item = get_category(session, user_id, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    return item


@router.patch("/{user_id}/{category_id}", response_model=CategoryOut)
def update(request: Request, user_id: UUID, category_id: UUID, payload: CategoryUpdate):
    session = request.app.state.cassandra_session
    item = update_category(session, user_id, category_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    return item


@router.delete("/{user_id}/{category_id}")
def delete(request: Request, user_id: UUID, category_id: UUID):
    session = request.app.state.cassandra_session
    delete_category(session, user_id, category_id)
    return {"deleted": True}

