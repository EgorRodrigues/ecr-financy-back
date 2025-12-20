from datetime import date
from typing import List
from sqlalchemy import select, func, case, and_, Text, cast
from sqlalchemy.orm import Session
from app.models.financial_forecast import ForecastItem
from app.db.postgres import incomes, expenses, categories

def get_financial_forecast(session: Session, start_date: date, end_date: date) -> List[ForecastItem]:
    results = []

    # Helper to format month
    def get_month_str(d):
        return d.strftime("%Y-%m")

    # --- Incomes ---
    # Determine effective date: receipt_date if received, else due_date
    inc_date_col = case(
        (incomes.c.status == 'recebido', incomes.c.receipt_date),
        else_=incomes.c.due_date
    )

    stmt_incomes = (
        select(
            incomes.c.id,
            inc_date_col.label("date"),
            incomes.c.amount,
            incomes.c.status,
            categories.c.name.label("category_name")
        )
        .outerjoin(categories, incomes.c.category_id == cast(categories.c.id, Text))
        .where(
            and_(
                incomes.c.status.in_(['pendente', 'recebido']),
                inc_date_col >= start_date,
                inc_date_col <= end_date
            )
        )
    )
    
    rows_incomes = session.execute(stmt_incomes).all()
    
    for row in rows_incomes:
        # Check if date is not null
        if not row.date:
            continue
            
        status_mapped = "confirmado" if row.status == "recebido" else "projetado"
        
        results.append(ForecastItem(
            id=str(row.id),
            month=get_month_str(row.date),
            category=row.category_name or "Sem Categoria",
            amount=float(row.amount or 0),
            status=status_mapped,
            type="income"
        ))

    # --- Expenses ---
    exp_date_col = case(
        (expenses.c.status == 'pago', expenses.c.payment_date),
        else_=expenses.c.due_date
    )

    stmt_expenses = (
        select(
            expenses.c.id,
            exp_date_col.label("date"),
            expenses.c.amount,
            expenses.c.status,
            categories.c.name.label("category_name")
        )
        .outerjoin(categories, expenses.c.category_id == cast(categories.c.id, Text))
        .where(
            and_(
                expenses.c.status.in_(['pendente', 'pago']),
                exp_date_col >= start_date,
                exp_date_col <= end_date
            )
        )
    )

    rows_expenses = session.execute(stmt_expenses).all()

    for row in rows_expenses:
        if not row.date:
            continue
            
        status_mapped = "confirmado" if row.status == "pago" else "projetado"
        
        results.append(ForecastItem(
            id=str(row.id),
            month=get_month_str(row.date),
            category=row.category_name or "Sem Categoria",
            amount=float(row.amount or 0),
            status=status_mapped,
            type="expense"
        ))

    # Sort by month
    results.sort(key=lambda x: x.month)
    
    return results
