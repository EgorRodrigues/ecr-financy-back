from datetime import date

from sqlalchemy import Text, and_, case, cast, func, select
from sqlalchemy.orm import Session

from app.models.categories import Category
from app.models.expenses import Expense
from app.models.incomes import Income
from app.schemas.financial_forecast import ForecastItem


def get_financial_forecast(
    session: Session, start_date: date, end_date: date
) -> list[ForecastItem]:
    results = []

    # --- Incomes ---
    # Determine effective date: receipt_date if received, else due_date
    inc_date_col = case(
        (
            and_(Income.status == "recebido", Income.receipt_date.is_not(None)),
            Income.receipt_date,
        ),
        else_=Income.due_date,
    )

    # Determine amount: total_received if received, else amount
    inc_amount_col = case(
        (
            Income.status == "recebido",
            func.coalesce(Income.total_received, Income.amount),
        ),
        else_=Income.amount,
    )

    # Dialect check for UUID join compatibility
    bind = session.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if is_sqlite:
        # Keep existing behavior for SQLite if it was working/intended
        join_cond_inc = Income.category_id == cast(Category.id, Text)
        join_cond_exp = Expense.category_id == cast(Category.id, Text)
    else:
        # Postgres: UUID = UUID
        join_cond_inc = Income.category_id == Category.id
        join_cond_exp = Expense.category_id == Category.id

    stmt_incomes = (
        select(
            Income.id,
            inc_date_col.label("date"),
            inc_amount_col.label("amount"),
            Income.status,
            Income.description,
            Category.name.label("category_name"),
        )
        .outerjoin(Category, join_cond_inc)
        .where(
            and_(
                Income.status.in_(["pendente", "recebido"]),
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
                month=str(row.date)[:7],
                category=row.category_name or "Sem Categoria",
                description=row.description,
                amount=float(row.amount or 0),
                status=status_mapped,
                type="income",
            )
        )

    # --- Expenses ---
    exp_date_col = case(
        (
            and_(Expense.status == "pago", Expense.payment_date.is_not(None)),
            Expense.payment_date,
        ),
        else_=Expense.due_date,
    )

    # Determine amount: total_paid if paid, else amount
    exp_amount_col = case(
        (
            Expense.status == "pago",
            func.coalesce(Expense.total_paid, Expense.amount),
        ),
        else_=Expense.amount,
    )

    stmt_expenses = (
        select(
            Expense.id,
            exp_date_col.label("date"),
            exp_amount_col.label("amount"),
            Expense.status,
            Expense.description,
            Category.name.label("category_name"),
        )
        .outerjoin(Category, join_cond_exp)
        .where(
            and_(
                Expense.status.in_(["pendente", "pago"]),
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
                month=str(row.date)[:7],
                category=row.category_name or "Sem Categoria",
                description=row.description,
                amount=float(row.amount or 0),
                status=status_mapped,
                type="expense",
            )
        )

    return results
