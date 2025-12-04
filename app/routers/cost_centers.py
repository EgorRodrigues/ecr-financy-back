from fastapi import APIRouter, HTTPException
from fastapi import Request
from uuid import UUID
from app.models.cost_centers import CostCenterCreate, CostCenterUpdate, CostCenterOut
from app.repositories.cost_centers import (
    create_cost_center,
    list_cost_centers,
    get_cost_center,
    update_cost_center,
    delete_cost_center,
)


router = APIRouter()


@router.post("/", response_model=CostCenterOut)
def create(request: Request, payload: CostCenterCreate):
    session = request.app.state.cassandra_session
    return create_cost_center(session, payload)


@router.get("/{user_id}", response_model=list[CostCenterOut])
def list_(request: Request, user_id: UUID, limit: int = 50):
    session = request.app.state.cassandra_session
    return list_cost_centers(session, user_id, limit)


@router.get("/{user_id}/{cost_center_id}", response_model=CostCenterOut)
def get(request: Request, user_id: UUID, cost_center_id: UUID):
    session = request.app.state.cassandra_session
    item = get_cost_center(session, user_id, cost_center_id)
    if not item:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return item


@router.patch("/{user_id}/{cost_center_id}", response_model=CostCenterOut)
def update(request: Request, user_id: UUID, cost_center_id: UUID, payload: CostCenterUpdate):
    session = request.app.state.cassandra_session
    item = update_cost_center(session, user_id, cost_center_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return item


@router.delete("/{user_id}/{cost_center_id}")
def delete(request: Request, user_id: UUID, cost_center_id: UUID):
    session = request.app.state.cassandra_session
    delete_cost_center(session, user_id, cost_center_id)
    return {"deleted": True}

