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


def _process_reconciliation(match_input: ReconciliationMatchInput, db: Session):
    # 1. Buscar todas as transações OFX
    ofx_transactions = db.query(OFXTransaction).filter(OFXTransaction.id.in_(match_input.ofx_transaction_ids)).all()
    if len(ofx_transactions) != len(match_input.ofx_transaction_ids):
        raise HTTPException(status_code=404, detail="Uma ou mais transações OFX não foram encontradas")

    # 2. Buscar todas as transações do sistema (Income ou Expense)
    if match_input.transaction_type == "income":
        transactions = db.query(Income).filter(Income.id.in_(match_input.transaction_ids)).all()
    else:
        transactions = db.query(Expense).filter(Expense.id.in_(match_input.transaction_ids)).all()

    if len(transactions) != len(match_input.transaction_ids):
        raise HTTPException(status_code=404, detail=f"Uma ou mais transações do tipo {match_input.transaction_type} não foram encontradas")

    # 3. Validar se os totais batem
    ofx_total = sum(t.amount for t in ofx_transactions)
    
    if match_input.transaction_type == "income":
        system_total = sum((t.total_received or t.amount) for t in transactions)
    else:
        system_total = sum((t.total_paid or t.amount) for t in transactions)

    if abs(abs(ofx_total) - abs(system_total)) > 0.01:
         raise HTTPException(
             status_code=400, 
             detail=f"Os valores não batem. Total OFX: {ofx_total:.2f}, Total Sistema: {system_total:.2f}"
         )

    today = date.today()
    
    # 4. Criar os registros de reconciliação
    for ofx in ofx_transactions:
        ofx.reconciled = True
        ofx.reconciliation_date = today
        ofx.reconciled_by = "user_id"

        for sys_trans in transactions:
            sys_trans.reconciled = True
            sys_trans.reconciliation_date = today
            sys_trans.reconciled_by = "user_id"

            reconciliation = Reconciliation(
                ofx_transaction_id=ofx.id,
                transaction_id=str(sys_trans.id),
                transaction_type=match_input.transaction_type,
                reconciliation_date=today,
                reconciled_by="user_id"
            )
            db.add(reconciliation)


@router.post("/reconcile-transactions")
def reconcile_transactions(match_input: ReconciliationMatchInput, db: Session = Depends(get_db)):
    _process_reconciliation(match_input, db)
    db.commit()
    return {"message": "Reconciliação concluída com sucesso."}


@router.post("/reconcile-batch-transactions")
def reconcile_batch_transactions(match_list: list[ReconciliationMatchInput], db: Session = Depends(get_db)):
    for match_input in match_list:
        _process_reconciliation(match_input, db)
    
    db.commit()
    return {"message": f"Reconciliação em lote concluída: {len(match_list)} grupos de transações processados."}
