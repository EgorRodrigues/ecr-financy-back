from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.subcategories import (
    SubcategoryCreate,
    SubcategoryOut,
    SubcategoryUpdate,
)
from app.repositories.subcategories import (
    create_subcategory,
    delete_subcategory,
    list_all_subcategories,
    update_subcategory,
)

router = APIRouter()


@router.post("/", response_model=SubcategoryOut)
def create(payload: SubcategoryCreate, session: Session = Depends(get_db)):
    return create_subcategory(session, payload)


@router.get("/", response_model=list[SubcategoryOut])
def list_all(limit: int = 100, session: Session = Depends(get_db)):
    return list_all_subcategories(session, limit)


@router.put("/{category_id}/{subcategory_id}", response_model=SubcategoryOut)
def update(
    category_id: UUID,
    subcategory_id: UUID,
    payload: SubcategoryUpdate,
    session: Session = Depends(get_db),
):
    item = update_subcategory(session, category_id, subcategory_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return item


@router.delete("/{category_id}/{subcategory_id}")
def delete(category_id: UUID, subcategory_id: UUID, session: Session = Depends(get_db)):
    delete_subcategory(session, category_id, subcategory_id)
    return {"deleted": True}
