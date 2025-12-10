from cassandra.query import PreparedStatement
from decimal import Decimal
from datetime import datetime, date
from app.models.dashboard import DashboardOut, BigNumbers, MonthlyItem, RecentTransaction


_prepared: dict[str, PreparedStatement] = {}


def _prepare(session, name: str, cql: str) -> PreparedStatement:
    if name not in _prepared:
        _prepared[name] = session.prepare(cql)
    return _prepared[name]


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


def get_dashboard_data(session, months: int = 6, recent_limit: int = 10) -> DashboardOut:
    stmt_incomes = _prepare(
        session,
        "dashboard_incomes",
        "SELECT id, amount, status, description, issue_date, due_date, receipt_date, total_received, created_at FROM incomes LIMIT ?",
    )
    stmt_expenses = _prepare(
        session,
        "dashboard_expenses",
        "SELECT id, amount, status, description, issue_date, due_date, payment_date, total_paid, created_at FROM expenses LIMIT ?",
    )
    incomes_rows = list(session.execute(stmt_incomes, (1000,)))
    expenses_rows = list(session.execute(stmt_expenses, (1000,)))

    approved = 0
    pending = 0
    failed = 0
    balance = 0.0

    monthly_map: dict[str, dict[str, float]] = {}
    recent_items: list[tuple[datetime, RecentTransaction]] = []

    for row in incomes_rows:
        status = getattr(row, "status", "pendente")
        if status == "recebido":
            approved += 1
            balance += _dec_to_float(getattr(row, "total_received", None) or getattr(row, "amount", None))
        elif status == "pendente":
            pending += 1
        else:
            failed += 1
        dt_index = _to_date(getattr(row, "receipt_date", None)) or _to_date(getattr(row, "issue_date", None)) or _to_date(getattr(row, "created_at", datetime.utcnow()))
        ms = _month_str(dt_index)
        mm = monthly_map.get(ms)
        if not mm:
            mm = {"inflows": 0.0, "outflows": 0.0}
            monthly_map[ms] = mm
        mm["inflows"] += _dec_to_float(getattr(row, "amount", None))
        rt = RecentTransaction(
            id=str(getattr(row, "id")),
            date=_to_date(getattr(row, "created_at", datetime.utcnow())).isoformat(),
            description=getattr(row, "description", "") or "",
            amount=_dec_to_float(getattr(row, "amount", None)),
            status=_income_status_en(status),
            type="income",
        )
        recent_items.append((getattr(row, "created_at", datetime.utcnow()), rt))

    for row in expenses_rows:
        status = getattr(row, "status", "pendente")
        if status == "pago":
            approved += 1
            balance -= _dec_to_float(getattr(row, "total_paid", None) or getattr(row, "amount", None))
        elif status == "pendente":
            pending += 1
        else:
            failed += 1
        dt_index = _to_date(getattr(row, "payment_date", None)) or _to_date(getattr(row, "issue_date", None)) or _to_date(getattr(row, "created_at", datetime.utcnow()))
        ms = _month_str(dt_index)
        mm = monthly_map.get(ms)
        if not mm:
            mm = {"inflows": 0.0, "outflows": 0.0}
            monthly_map[ms] = mm
        mm["outflows"] += _dec_to_float(getattr(row, "amount", None))
        rt = RecentTransaction(
            id=str(getattr(row, "id")),
            date=_to_date(getattr(row, "created_at", datetime.utcnow())).isoformat(),
            description=getattr(row, "description", "") or "",
            amount=_dec_to_float(getattr(row, "amount", None)),
            status=_expense_status_en(status),
            type="expense",
        )
        recent_items.append((getattr(row, "created_at", datetime.utcnow()), rt))

    months_sorted = sorted(monthly_map.keys())
    months_selected = months_sorted[-months:] if months > 0 else months_sorted
    monthly = [
        MonthlyItem(month=m, inflows=monthly_map[m]["inflows"], outflows=monthly_map[m]["outflows"])
        for m in months_selected
    ]

    recent_items.sort(key=lambda x: x[0], reverse=True)
    recent_transactions = [ri[1] for ri in recent_items[:recent_limit]]

    bn = BigNumbers(balance=balance, approved=approved, pending=pending, failed=failed)
    return DashboardOut(big_numbers=bn, monthly=monthly, recent_transactions=recent_transactions)

