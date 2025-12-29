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
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return create_category(session, payload)


@router.get("/", response_model=list[CategoryOut])
def list_(request: Request, limit: int = 50):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_categories(session, limit)


@router.get("/{category_id}", response_model=CategoryOut)
def get(request: Request, category_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = get_category(session, category_id)
        if not item:
            raise HTTPException(status_code=404, detail="Category not found")
        return item


@router.put("/{category_id}", response_model=CategoryOut)
def update(request: Request, category_id: UUID, payload: CategoryUpdate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = update_category(session, category_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Category not found")
        return item


@router.delete("/{category_id}")
def delete(request: Request, category_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        delete_category(session, category_id)
    return {"deleted": True}
