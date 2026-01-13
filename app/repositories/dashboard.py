from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select

from app.db.postgres import expenses, incomes
from app.models.dashboard import BigNumbers, DashboardOut, MonthlyItem, RecentTransaction


def _to_date(value):
    return value.date() if hasattr(value, "date") else value


def _month_str(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _dec_to_float(v: Decimal | None) -> float:
    return float(v if v is not None else Decimal("0"))


def _income_status_en(s: str) -> str:
    if s == "recebido":
        return "received"
    if s == "pendente":
        return "pending"
    return "failed"


def _expense_status_en(s: str) -> str:
    if s == "pago":
        return "paid"
    if s == "pendente":
        return "pending"
    return "failed"


def _fetch_incomes(session):
    return list(
        session.execute(
            select(
                incomes.c.id,
                incomes.c.amount,
                incomes.c.status,
                incomes.c.description,
                incomes.c.issue_date,
                incomes.c.due_date,
                incomes.c.receipt_date,
                incomes.c.total_received,
                incomes.c.created_at,
            ).limit(1000)
        )
    )


def _fetch_expenses(session):
    return list(
        session.execute(
            select(
                expenses.c.id,
                expenses.c.amount,
                expenses.c.status,
                expenses.c.description,
                expenses.c.issue_date,
                expenses.c.due_date,
                expenses.c.payment_date,
                expenses.c.total_paid,
                expenses.c.created_at,
            ).limit(1000)
        )
    )


def _process_incomes(rows, stats, monthly_map, recent_items):
    for row in rows:
        status = getattr(row, "status", "pendente")
        if status == "recebido":
            stats["approved"] += 1
            stats["balance"] += _dec_to_float(
                getattr(row, "total_received", None) or getattr(row, "amount", None)
            )
        elif status == "pendente":
            stats["pending"] += 1
        else:
            stats["failed"] += 1
        dt_index = (
            _to_date(getattr(row, "receipt_date", None))
            or _to_date(getattr(row, "due_date", None))
            or _to_date(getattr(row, "created_at", datetime.utcnow()))
        )
        ms = _month_str(dt_index)
        mm = monthly_map.get(ms)
        if not mm:
            mm = {"inflows": 0.0, "outflows": 0.0}
            monthly_map[ms] = mm
        mm["inflows"] += _dec_to_float(getattr(row, "amount", None))
        rt = RecentTransaction(
            id=str(row.id),
            date=_to_date(getattr(row, "created_at", datetime.utcnow())).isoformat(),
            description=getattr(row, "description", "") or "",
            amount=_dec_to_float(getattr(row, "amount", None)),
            status=_income_status_en(status),
            type="income",
        )
        recent_items.append((getattr(row, "created_at", datetime.utcnow()), rt))


def _process_expenses(rows, stats, monthly_map, recent_items):
    for row in rows:
        status = getattr(row, "status", "pendente")
        if status == "pago":
            stats["approved"] += 1
            stats["balance"] -= _dec_to_float(
                getattr(row, "total_paid", None) or getattr(row, "amount", None)
            )
        elif status == "pendente":
            stats["pending"] += 1
        else:
            stats["failed"] += 1
        dt_index = (
            _to_date(getattr(row, "payment_date", None))
            or _to_date(getattr(row, "due_date", None))
            or _to_date(getattr(row, "created_at", datetime.utcnow()))
        )
        ms = _month_str(dt_index)
        mm = monthly_map.get(ms)
        if not mm:
            mm = {"inflows": 0.0, "outflows": 0.0}
            monthly_map[ms] = mm
        mm["outflows"] += _dec_to_float(getattr(row, "amount", None))
        rt = RecentTransaction(
            id=str(row.id),
            date=_to_date(getattr(row, "created_at", datetime.utcnow())).isoformat(),
            description=getattr(row, "description", "") or "",
            amount=_dec_to_float(getattr(row, "amount", None)),
            status=_expense_status_en(status),
            type="expense",
        )
        recent_items.append((getattr(row, "created_at", datetime.utcnow()), rt))


def _build_dashboard_response(stats, monthly_map, recent_items, months, recent_limit):
    current_month_str = _month_str(datetime.utcnow().date())
    months_sorted = sorted([m for m in monthly_map.keys() if m <= current_month_str])
    months_selected = months_sorted[-months:] if months > 0 else months_sorted
    monthly = [
        MonthlyItem(month=m, inflows=monthly_map[m]["inflows"], outflows=monthly_map[m]["outflows"])
        for m in months_selected
    ]

    recent_items.sort(key=lambda x: x[0], reverse=True)
    recent_transactions = [ri[1] for ri in recent_items[:recent_limit]]

    bn = BigNumbers(
        balance=stats["balance"],
        approved=stats["approved"],
        pending=stats["pending"],
        failed=stats["failed"],
    )
    return DashboardOut(big_numbers=bn, monthly=monthly, recent_transactions=recent_transactions)


def get_dashboard_data(session, months: int = 6, recent_limit: int = 10) -> DashboardOut:
    incomes_rows = _fetch_incomes(session)
    expenses_rows = _fetch_expenses(session)

    stats = {"approved": 0, "pending": 0, "failed": 0, "balance": 0.0}
    monthly_map: dict[str, dict[str, float]] = {}
    recent_items: list[tuple[datetime, RecentTransaction]] = []

    _process_incomes(incomes_rows, stats, monthly_map, recent_items)
    _process_expenses(expenses_rows, stats, monthly_map, recent_items)

    return _build_dashboard_response(stats, monthly_map, recent_items, months, recent_limit)
