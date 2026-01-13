from datetime import date
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.db.postgres import expenses, categories, accounts
from app.models.reporting import ExpenseByCategoryAndAccount


def get_expenses_by_category_account(
    session: Session, start_date: date | None, end_date: date | None
) -> list[ExpenseByCategoryAndAccount]:
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
            expenses.c.account,
            func.sum(expenses.c.amount).label("total_amount"),
        )
        .where(and_(*conditions))
        .group_by(expenses.c.category_id, expenses.c.account)
    )

    rows = session.execute(stmt).all()

    acc_rows = session.execute(select(accounts.c.id, accounts.c.name)).all()
    acc_id_to_name = {str(r.id): r.name for r in acc_rows}
    acc_name_to_id = {r.name: str(r.id) for r in acc_rows}

    results: list[ExpenseByCategoryAndAccount] = []
    for row in rows:
        cid = row.category_id if row.category_id is not None else ""
        raw_acc = row.account or ""

        if raw_acc in acc_id_to_name:
            account_id = raw_acc
            account_name = acc_id_to_name[raw_acc]
        elif raw_acc in acc_name_to_id:
            account_id = acc_name_to_id[raw_acc]
            account_name = raw_acc
        else:
            account_id = ""
            account_name = raw_acc or "Sem Conta"

        total = float(row.total_amount if isinstance(row.total_amount, Decimal) else row.total_amount or 0)
        results.append(
            ExpenseByCategoryAndAccount(
                category_id=str(cid),
                category_name=cat_map.get(str(cid), "Sem Categoria"),
                account_id=account_id,
                account_name=account_name,
                total_amount=total,
            )
        )

    return results

