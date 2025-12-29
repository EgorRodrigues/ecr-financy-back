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
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return create_cost_center(session, payload)


@router.get("/", response_model=list[CostCenterOut])
def list_(request: Request, limit: int = 50):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_cost_centers(session, limit)


@router.get("/{cost_center_id}", response_model=CostCenterOut)
def get(request: Request, cost_center_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = get_cost_center(session, cost_center_id)
        if not item:
            raise HTTPException(status_code=404, detail="Cost center not found")
        return item


@router.patch("/{cost_center_id}", response_model=CostCenterOut)
def update(request: Request, cost_center_id: UUID, payload: CostCenterUpdate):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = update_cost_center(session, cost_center_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Cost center not found")
        return item


@router.delete("/{cost_center_id}")
def delete(request: Request, cost_center_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        delete_cost_center(session, cost_center_id)
    return {"deleted": True}
