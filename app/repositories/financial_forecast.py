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

    # Adjust start_date and end_date to cover full financial months
    # Financial Month X starts on (Month X-1)-start_day and ends on (Month X)-end_day

    # 1. Adjust Start Date
    s_day = start_date.day
    s_month = start_date.month
    s_year = start_date.year
    start_day = 16
    end_day = 15

    if s_day >= start_day:
        # Already in the new financial month. Start is 26th of current month.
        start_date = date(s_year, s_month, start_day)
    else:
        # In the main body. Start is 26th of previous month.
        if s_month == 1:
            start_date = date(s_year - 1, 12, start_day)
        else:
            start_date = date(s_year, s_month - 1, start_day)

    # 2. Adjust End Date
    e_day = end_date.day
    e_month = end_date.month
    e_year = end_date.year

    if e_day >= 26:
        # In the new financial month. End is 25th of next month.
        if e_month == 12:
            end_date = date(e_year + 1, 1, end_day)
        else:
            end_date = date(e_year, e_month + 1, end_day)
    else:
        # In the main body. End is 25th of current month.
        end_date = date(e_year, e_month, end_day)

    # Helper to determine cash flow period
    # Logic: Income from 1st fortnight pays for 2nd fortnight expenses.
    #        Income from 2nd fortnight pays for next month's 1st fortnight expenses.
    def get_period_str(d: date) -> str:
        year = d.year
        month = d.month
        day = d.day

        # Financial month starts on the 26th of the previous month.
        if day >= start_day:
            month += 1
            if month > 12:
                month = 1
                year += 1

        return f"{year}-{month:02d}"

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

    stmt_incomes = (
        select(
            Income.id,
            inc_date_col.label("date"),
            inc_amount_col.label("amount"),
            Income.status,
            Category.name.label("category_name"),
        )
        .outerjoin(Category, Income.category_id == cast(Category.id, Text))
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
                month=get_period_str(row.date),
                category=row.category_name or "Sem Categoria",
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
            Category.name.label("category_name"),
        )
        .outerjoin(Category, Expense.category_id == cast(Category.id, Text))
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
                month=get_period_str(row.date),
                category=row.category_name or "Sem Categoria",
                amount=float(row.amount or 0),
                status=status_mapped,
                type="expense",
            )
        )

    # Sort by month
    results.sort(key=lambda x: x.month)

    return results
