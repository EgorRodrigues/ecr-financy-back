from datetime import date
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.postgres import contacts, incomes
from app.models.reporting import IncomeByCustomer


def get_incomes_by_customer(
    session: Session, start_date: date | None, end_date: date | None
) -> list[IncomeByCustomer]:
    conditions = [incomes.c.status == "recebido"]
    if start_date is not None:
        conditions.append(
            func.coalesce(incomes.c.receipt_date, incomes.c.due_date, incomes.c.issue_date)
            >= start_date
        )
    if end_date is not None:
        conditions.append(
            func.coalesce(incomes.c.receipt_date, incomes.c.due_date, incomes.c.issue_date)
            <= end_date
        )

    ct_rows = session.execute(select(contacts.c.id, contacts.c.name)).all()
    ct_map = {str(r.id): r.name for r in ct_rows}

    sum_col = func.sum(func.coalesce(incomes.c.total_received, incomes.c.amount)).label(
        "total_amount"
    )

    stmt = (
        select(
            incomes.c.contact_id,
            sum_col,
        )
        .where(and_(*conditions))
        .group_by(incomes.c.contact_id)
    )

    rows = session.execute(stmt).all()

    results: list[IncomeByCustomer] = []
    for row in rows:
        cid = row.contact_id if row.contact_id is not None else ""
        total = float(
            row.total_amount if isinstance(row.total_amount, Decimal) else row.total_amount or 0
        )
        results.append(
            IncomeByCustomer(
                contact_id=str(cid),
                contact_name=ct_map.get(str(cid), "Sem Cliente"),
                total_amount=total,
            )
        )

    return results
