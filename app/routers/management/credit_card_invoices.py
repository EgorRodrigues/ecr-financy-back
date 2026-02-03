from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.credit_card_invoices import (
    CreditCardInvoiceCreate,
    CreditCardInvoiceOut,
    CreditCardInvoiceUpdate,
)
from app.repositories.credit_card_invoices import (
    create_invoice,
    delete_invoice,
    get_invoice,
    list_invoices,
    update_invoice,
)

router = APIRouter()


@router.get("/", response_model=list[CreditCardInvoiceOut])
def list_(
    limit: int = 50,
    account_id: UUID | None = None,
    status: str | None = None,
    session: Session = Depends(get_db),
):
    return list_invoices(session, account_id, status, limit)


@router.post("/", response_model=CreditCardInvoiceOut, status_code=status.HTTP_201_CREATED)
def create(payload: CreditCardInvoiceCreate, session: Session = Depends(get_db)):
    try:
        invoice = create_invoice(session, payload)
        session.commit()
        return invoice
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{invoice_id}", response_model=CreditCardInvoiceOut)
def get(invoice_id: UUID, session: Session = Depends(get_db)):
    item = get_invoice(session, invoice_id)
    if not item:
        raise HTTPException(status_code=404, detail="Credit Card Invoice not found")
    return item


@router.put("/{invoice_id}", response_model=CreditCardInvoiceOut)
def update(invoice_id: UUID, payload: CreditCardInvoiceUpdate, session: Session = Depends(get_db)):
    try:
        item = update_invoice(session, invoice_id, payload)
        if not item:
            raise HTTPException(status_code=404, detail="Credit Card Invoice not found")
        session.commit()
        return item
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(invoice_id: UUID, session: Session = Depends(get_db)):
    try:
        result = delete_invoice(session, invoice_id)
        if not result:
            pass
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
