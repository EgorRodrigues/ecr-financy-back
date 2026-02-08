from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.accounts import Account
from app.models.expenses import Expense
from app.models.incomes import Income
from app.schemas.transfers import TransferCreate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransferCreate, session: Session = Depends(get_db)):
    # 1. Validate Accounts
    source_account = session.get(Account, payload.source_account_id)
    destination_account = session.get(Account, payload.destination_account_id)

    if not source_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    if not destination_account:
        raise HTTPException(status_code=404, detail="Destination account not found")

    if source_account.id == destination_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    # 2. Determine Contacts (Supplier/Customer)
    # Expense Supplier = Destination Account's Contact (e.g. "Nubank")
    # Income Customer = Source Account's Contact (e.g. "Itaú")
    expense_contact_id = destination_account.contact_id
    income_contact_id = source_account.contact_id

    # 3. Create Expense (Money leaving source)
    description = payload.description or f"Transferência para {destination_account.name}"
    
    expense = Expense(
        id=uuid4(),
        amount=payload.amount,
        status="pago", # Transfers are immediate usually
        total_paid=payload.amount,
        issue_date=payload.date,
        due_date=payload.date,
        payment_date=payload.date,
        description=description,
        account_id=source_account.id,
        contact_id=expense_contact_id,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        cost_center_id=payload.cost_center_id,
        project=payload.project,
        competence=payload.competence,
        tags=payload.tags,
        active=True
    )
    session.add(expense)

    # 4. Create Income (Money entering destination)
    income_description = payload.description or f"Transferência de {source_account.name}"

    income = Income(
        id=uuid4(),
        amount=payload.amount,
        status="recebido", # Transfers are immediate usually
        total_received=payload.amount,
        issue_date=payload.date,
        due_date=payload.date,
        receipt_date=payload.date,
        description=income_description,
        account_id=destination_account.id,
        contact_id=income_contact_id,
        category_id=payload.category_id,
        subcategory_id=payload.subcategory_id,
        cost_center_id=payload.cost_center_id,
        project=payload.project,
        competence=payload.competence,
        tags=payload.tags,
        active=True
    )
    session.add(income)
    
    # 5. Commit
    expense_id = expense.id
    income_id = income.id
    session.commit()
    
    return {"message": "Transfer created successfully", "expense_id": expense_id, "income_id": income_id}
