from datetime import date
from typing import List
from sqlalchemy import select, case, and_, Text, cast
from sqlalchemy.orm import Session
from app.models.financial_forecast import ForecastItem
from app.db.postgres import incomes, expenses, categories


def get_financial_forecast(
    session: Session, start_date: date, end_date: date
) -> List[ForecastItem]:
    results = []

    # Helper to determine cash flow period (fortnightly)
    # Logic: Income from 1st fortnight pays for 2nd fortnight expenses.
    #        Income from 2nd fortnight pays for next month's 1st fortnight expenses.
    def get_period_str(d: date, is_income: bool = False) -> str:
        year = d.year
        month = d.month
        day = d.day

        # Determine current fortnight (1 or 2)
        fortnight = 1 if day <= 15 else 2

        if is_income:
            # Shift income forward by one fortnight
            if fortnight == 1:
                fortnight = 2
            else:
                fortnight = 1
                month += 1
                if month > 12:
                    month = 1
                    year += 1

        return f"{year}-{month:02d}-Q{fortnight}"

    # --- Incomes ---
    # Determine effective date: receipt_date if received, else due_date
    inc_date_col = case(
        (
            and_(incomes.c.status == "recebido", incomes.c.receipt_date.is_not(None)),
            incomes.c.receipt_date,
        ),
        else_=incomes.c.due_date,
    )

    stmt_incomes = (
        select(
            incomes.c.id,
            inc_date_col.label("date"),
            incomes.c.amount,
            incomes.c.status,
            categories.c.name.label("category_name"),
        )
        .outerjoin(categories, incomes.c.category_id == cast(categories.c.id, Text))
        .where(
            and_(
                incomes.c.status.in_(["pendente", "recebido"]),
                inc_date_col >= start_date,
                inc_date_col <= end_date,
            )
        )
    )

    rows_incomes = session.execute(stmt_incomes).all()

    for row in rows_incomes:
        # Check if date is not null
        if not row.date:
            continue

        status_mapped = "confirmado" if row.status == "recebido" else "projetado"

        results.append(
            ForecastItem(
                id=str(row.id),
                month=get_period_str(row.date, is_income=True),
                category=row.category_name or "Sem Categoria",
                amount=float(row.amount or 0),
                status=status_mapped,
                type="income",
            )
        )

    # --- Expenses ---
    exp_date_col = case(
        (
            and_(expenses.c.status == "pago", expenses.c.payment_date.is_not(None)),
            expenses.c.payment_date,
        ),
        else_=expenses.c.due_date,
    )

    stmt_expenses = (
        select(
            expenses.c.id,
            exp_date_col.label("date"),
            expenses.c.amount,
            expenses.c.status,
            categories.c.name.label("category_name"),
        )
        .outerjoin(categories, expenses.c.category_id == cast(categories.c.id, Text))
        .where(
            and_(
                expenses.c.status.in_(["pendente", "pago"]),
                exp_date_col >= start_date,
                exp_date_col <= end_date,
            )
        )
    )

    rows_expenses = session.execute(stmt_expenses).all()

    for row in rows_expenses:
        if not row.date:
            continue

        status_mapped = "confirmado" if row.status == "pago" else "projetado"

        results.append(
            ForecastItem(
                id=str(row.id),
                month=get_period_str(row.date, is_income=False),
                category=row.category_name or "Sem Categoria",
                amount=float(row.amount or 0),
                status=status_mapped,
                type="expense",
            )
        )

    # Sort by month
    results.sort(key=lambda x: x.month)

    return results
