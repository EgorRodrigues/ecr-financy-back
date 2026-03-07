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
def get_unreconciled_ofx_transactions(db: Session = Depends(get_db)):
    return db.query(OFXTransaction).filter(OFXTransaction.reconciled == False).all()


@router.get("/unreconciled-transactions", response_model=dict[str, list[IncomeSchema] | list[ExpenseSchema]])
def get_unreconciled_transactions(db: Session = Depends(get_db)):
    incomes = db.query(Income).filter(Income.reconciled == False).all()
    expenses = db.query(Expense).filter(Expense.reconciled == False).all()
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
