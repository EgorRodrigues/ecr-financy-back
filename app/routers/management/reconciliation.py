from datetime import date
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.ofx_service import OFXService
from app.dependencies import get_db
from app.models.ofx_transaction import OFXTransaction
from app.models.incomes import Income
from app.models.expenses import Expense
from app.models.reconciliation import Reconciliation
from app.schemas.reconciliation import (
    OFXImportResponse,
    OFXTransaction as OFXTransactionSchema,
    Income as IncomeSchema,
    Expense as ExpenseSchema,
    ReconciliationMatchInput,
)

router = APIRouter()


@router.post("/import-ofx", response_model=OFXImportResponse)
async def import_ofx(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".ofx"):
        raise HTTPException(status_code=400, detail="Somente arquivos .ofx são permitidos")

    try:
        content = await file.read()
        import io
        service = OFXService(db)
        return service.parse_and_save_ofx(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar arquivo OFX: {str(e)}")


@router.get("/unreconciled-ofx-transactions", response_model=list[OFXTransactionSchema])
def get_unreconciled_ofx_transactions(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(OFXTransaction).filter(OFXTransaction.reconciled == False)

    if start_date:
        query = query.filter(OFXTransaction.date >= start_date)

    if end_date:
        query = query.filter(OFXTransaction.date <= end_date)

    return query.all()


@router.get("/unreconciled-transactions", response_model=dict[str, list[IncomeSchema] | list[ExpenseSchema]])
def get_unreconciled_transactions(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db)
):
    income_query = db.query(Income).filter(
        Income.reconciled == False, 
        Income.status == "recebido",
        Income.active == True
    )
    expense_query = db.query(Expense).filter(
        Expense.reconciled == False, 
        Expense.status == "pago",
        Expense.active == True
    )

    if start_date:
        income_query = income_query.filter(Income.receipt_date >= start_date)
        expense_query = expense_query.filter(Expense.payment_date >= start_date)

    if end_date:
        income_query = income_query.filter(Income.receipt_date <= end_date)
        expense_query = expense_query.filter(Expense.payment_date <= end_date)

    incomes = income_query.all()
    expenses = expense_query.all()
    return {"incomes": incomes, "expenses": expenses}


@router.post("/reconcile-transactions")
def reconcile_transactions(match_input: ReconciliationMatchInput, db: Session = Depends(get_db)):
    ofx_transaction = db.query(OFXTransaction).filter(OFXTransaction.id == match_input.ofx_transaction_id).first()
    if not ofx_transaction:
        raise HTTPException(status_code=404, detail="OFX transaction not found")

    if match_input.transaction_type == "income":
        transaction = db.query(Income).filter(Income.id == match_input.transaction_id).first()
    else:
        transaction = db.query(Expense).filter(Expense.id == match_input.transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    ofx_transaction.reconciled = True
    transaction.reconciled = True

    reconciliation = Reconciliation(
        ofx_transaction_id=ofx_transaction.id,
        transaction_id=transaction.id,
        transaction_type=match_input.transaction_type,
        reconciliation_date=date.today(),
        reconciled_by="user_id"  # Substituir pelo ID do usuário autenticado
    )

    db.add(reconciliation)
    db.commit()

    return {"message": "Transactions reconciled successfully"}
