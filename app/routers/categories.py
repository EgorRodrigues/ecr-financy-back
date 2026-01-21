from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.categories import CategoryCreate, CategoryOut, CategoryUpdate
from app.repositories.categories import (
    create_category,
    delete_category,
    get_category,
    list_categories,
    update_category,
)

router = APIRouter()


@router.post("/", response_model=CategoryOut)
def create(payload: CategoryCreate, session: Session = Depends(get_db)):
    return create_category(session, payload)


@router.get("/", response_model=list[CategoryOut])
def list_(limit: int = 500, session: Session = Depends(get_db)):
    return list_categories(session, limit)


@router.get("/{category_id}", response_model=CategoryOut)
def get(category_id: UUID, session: Session = Depends(get_db)):
    item = get_category(session, category_id)
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    return item


@router.put("/{category_id}", response_model=CategoryOut)
def update(category_id: UUID, payload: CategoryUpdate, session: Session = Depends(get_db)):
    item = update_category(session, category_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Category not found")
    return item


@router.delete("/{category_id}")
def delete(category_id: UUID, session: Session = Depends(get_db)):
    delete_category(session, category_id)
    return {"deleted": True}
