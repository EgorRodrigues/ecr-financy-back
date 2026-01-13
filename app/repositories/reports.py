from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, and_, union_all
from sqlalchemy.orm import Session
from app.db.postgres import expenses, categories, credit_card_transactions
from app.models.reports import ExpenseByCategory


def get_expenses_by_category(
    session: Session, start_date: date | None, end_date: date | None
) -> list[ExpenseByCategory]:
    # Conditions for regular expenses (paid)
    conditions_expenses = [expenses.c.status == "pago"]
    if start_date is not None:
        conditions_expenses.append(expenses.c.payment_date >= start_date)
    if end_date is not None:
        conditions_expenses.append(expenses.c.payment_date <= end_date)

    # Conditions for credit card transactions (launched)
    # Assuming we want to see expenses when they were made (issue_date)
    conditions_cc = []
    if start_date is not None:
        conditions_cc.append(credit_card_transactions.c.issue_date >= start_date)
    if end_date is not None:
        conditions_cc.append(credit_card_transactions.c.issue_date <= end_date)

    cats = session.execute(select(categories.c.id, categories.c.name)).all()
    cat_map = {str(c.id): c.name for c in cats}

    stmt_expenses = (
        select(
            expenses.c.category_id,
            func.sum(expenses.c.amount).label("amount"),
        )
        .where(and_(*conditions_expenses))
        .group_by(expenses.c.category_id)
    )

    stmt_cc = (
        select(
            credit_card_transactions.c.category_id,
            func.sum(credit_card_transactions.c.amount).label("amount"),
        )
        .group_by(credit_card_transactions.c.category_id)
    )
    if conditions_cc:
        stmt_cc = stmt_cc.where(and_(*conditions_cc))

    # Combine both queries
    union_query = union_all(stmt_expenses, stmt_cc).subquery()

    final_stmt = (
        select(
            union_query.c.category_id,
            func.sum(union_query.c.amount).label("total_amount"),
        )
        .group_by(union_query.c.category_id)
    )

    rows = session.execute(final_stmt).all()

    results: list[ExpenseByCategory] = []
    for row in rows:
        cid = row.category_id if row.category_id is not None else ""
        total = float(row.total_amount if isinstance(row.total_amount, Decimal) else row.total_amount or 0)
        results.append(
            ExpenseByCategory(
                category_id=str(cid),
                category_name=cat_map.get(str(cid), "Sem Categoria"),
                total_amount=total,
            )
        )

    return results
