from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.db.postgres import expenses, categories
from app.models.reports import ExpenseByCategory


def get_expenses_by_category(
    session: Session, start_date: date | None, end_date: date | None
) -> list[ExpenseByCategory]:
    conditions = [expenses.c.status == "pago"]
    if start_date is not None:
        conditions.append(expenses.c.payment_date >= start_date)
    if end_date is not None:
        conditions.append(expenses.c.payment_date <= end_date)

    cats = session.execute(select(categories.c.id, categories.c.name)).all()
    cat_map = {str(c.id): c.name for c in cats}

    stmt = (
        select(
            expenses.c.category_id,
            func.sum(expenses.c.amount).label("total_amount"),
        )
        .where(and_(*conditions))
        .group_by(expenses.c.category_id)
    )

    rows = session.execute(stmt).all()

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

