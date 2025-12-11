from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.subcategories import SubcategoryCreate, SubcategoryUpdate, SubcategoryOut, SubcategoryMove
from app.repositories.subcategories import (
    create_subcategory,
    list_subcategories,
    list_all_subcategories,
    get_subcategory,
    update_subcategory,
    delete_subcategory,
    move_subcategory,
)


router = APIRouter()


@router.post("/", response_model=SubcategoryOut)
def create(request: Request, payload: SubcategoryCreate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return create_subcategory(session, payload)


@router.get("/", response_model=list[SubcategoryOut])
def list_all(request: Request, limit: int = 50):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_all_subcategories(session, limit)


@router.get("/{category_id}", response_model=list[SubcategoryOut])
def list_(request: Request, category_id: UUID, limit: int = 50):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_subcategories(session, category_id, limit)


@router.get("/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def get(request: Request, category_id: UUID, subcategory_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = get_subcategory(session, category_id, subcategory_id)
        if not item:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        return item


@router.put("/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def update(request: Request, category_id: UUID, subcategory_id: UUID, payload: SubcategoryUpdate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = update_subcategory(session, category_id, subcategory_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        return item


@router.delete("/{category_id}/{subcategory_id}")
def delete(request: Request, category_id: UUID, subcategory_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        delete_subcategory(session, category_id, subcategory_id)
    return {"deleted": True}


@router.post("/{category_id}/{subcategory_id}/move", response_model=SubcategoryOut)
def move(request: Request, category_id: UUID, subcategory_id: UUID, payload: SubcategoryMove):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = move_subcategory(session, category_id, subcategory_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        return item
