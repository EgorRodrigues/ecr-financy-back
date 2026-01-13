from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.cost_centers import CostCenterCreate, CostCenterOut, CostCenterUpdate
from app.repositories.cost_centers import (
    create_cost_center,
    delete_cost_center,
    get_cost_center,
    list_cost_centers,
    update_cost_center,
)

router = APIRouter()


@router.post("/", response_model=CostCenterOut)
def create(payload: CostCenterCreate, session: Session = Depends(get_db)):
    return create_cost_center(session, payload)


@router.get("/", response_model=list[CostCenterOut])
def list_(limit: int = 50, session: Session = Depends(get_db)):
    return list_cost_centers(session, limit)


@router.get("/{cost_center_id}", response_model=CostCenterOut)
def get(cost_center_id: UUID, session: Session = Depends(get_db)):
    item = get_cost_center(session, cost_center_id)
    if not item:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return item


@router.patch("/{cost_center_id}", response_model=CostCenterOut)
def update(cost_center_id: UUID, payload: CostCenterUpdate, session: Session = Depends(get_db)):
    item = update_cost_center(session, cost_center_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return item


@router.delete("/{cost_center_id}")
def delete(cost_center_id: UUID, session: Session = Depends(get_db)):
    delete_cost_center(session, cost_center_id)
    return {"deleted": True}
