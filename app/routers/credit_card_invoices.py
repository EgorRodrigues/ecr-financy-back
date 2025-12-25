from fastapi import APIRouter, HTTPException, Request
from uuid import UUID
from app.models.credit_card_invoices import CreditCardInvoiceOut
from app.repositories.credit_card_invoices import (
    list_invoices,
    get_invoice
)

router = APIRouter()

@router.get("/", response_model=list[CreditCardInvoiceOut])
def list_(request: Request, limit: int = 50, account_id: UUID | None = None, status: str | None = None):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        return list_invoices(session, account_id, status, limit)

@router.get("/{invoice_id}", response_model=CreditCardInvoiceOut)
def get(request: Request, invoice_id: UUID):
    SessionLocal = request.app.state.cassandra_session
    with SessionLocal() as session:
        item = get_invoice(session, invoice_id)
        if not item:
            raise HTTPException(status_code=404, detail="Credit Card Invoice not found")
        return item
