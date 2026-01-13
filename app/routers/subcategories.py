from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.subcategories import (
    SubcategoryCreate,
    SubcategoryUpdate,
    SubcategoryOut,
    SubcategoryMove,
)
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
def create(payload: SubcategoryCreate, session: Session = Depends(get_db)):
    return create_subcategory(session, payload)


@router.get("/", response_model=list[SubcategoryOut])
def list_all(limit: int = 50, session: Session = Depends(get_db)):
    return list_all_subcategories(session, limit)


@router.get("/{category_id}", response_model=list[SubcategoryOut])
def list_(category_id: UUID, limit: int = 50, session: Session = Depends(get_db)):
    return list_subcategories(session, category_id, limit)


@router.get("/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def get(category_id: UUID, subcategory_id: UUID, session: Session = Depends(get_db)):
    item = get_subcategory(session, category_id, subcategory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return item


@router.put("/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def update(category_id: UUID, subcategory_id: UUID, payload: SubcategoryUpdate, session: Session = Depends(get_db)):
    item = update_subcategory(session, category_id, subcategory_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return item


@router.delete("/{category_id}/{subcategory_id}")
def delete(category_id: UUID, subcategory_id: UUID, session: Session = Depends(get_db)):
    delete_subcategory(session, category_id, subcategory_id)
    return {"deleted": True}


@router.post("/{category_id}/{subcategory_id}/move", response_model=SubcategoryOut)
def move(category_id: UUID, subcategory_id: UUID, payload: SubcategoryMove, session: Session = Depends(get_db)):
    item = move_subcategory(session, category_id, subcategory_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return item
