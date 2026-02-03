from datetime import date, timedelta

from sqlalchemy import Text, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.db.postgres import accounts, expenses, incomes
from app.models.dashboard import (
    DashboardAccount,
    DashboardResponse,
    MonthlySummary,
    RecentTransaction,
)


def get_dashboard_data(session: Session) -> DashboardResponse:
    # 1. Accounts with Balance
    inc_sub = (
        select(
            func.cast(incomes.c.account, Text).label("account_id"),
            func.sum(incomes.c.amount).label("total_income"),
        )
        .where(incomes.c.active == True)
        .group_by(incomes.c.account)
        .subquery()
    )

    exp_sub = (
        select(
            func.cast(expenses.c.account, Text).label("account_id"),
            func.sum(expenses.c.amount).label("total_expense"),
        )
        .where(expenses.c.active == True)
        .group_by(expenses.c.account)
        .subquery()
    )

    # Dialect check for UUID join compatibility
    dialect = session.get_bind().dialect.name
    if dialect == "sqlite":
        join_inc = func.replace(inc_sub.c.account_id, "-", "") == func.cast(
            accounts.c.id, Text
        )
        join_exp = func.replace(exp_sub.c.account_id, "-", "") == func.cast(
            accounts.c.id, Text
        )
    else:
        join_inc = func.cast(accounts.c.id, Text) == inc_sub.c.account_id
        join_exp = func.cast(accounts.c.id, Text) == exp_sub.c.account_id

    stmt_accounts = (
        select(
            accounts.c.id,
            accounts.c.name,
            accounts.c.initial_balance,
            accounts.c.type,
            func.coalesce(inc_sub.c.total_income, 0).label("income_sum"),
            func.coalesce(exp_sub.c.total_expense, 0).label("expense_sum"),
        )
        .outerjoin(inc_sub, join_inc)
        .outerjoin(exp_sub, join_exp)
        .where(accounts.c.active == True)
    )

    acct_rows = session.execute(stmt_accounts).all()

    dashboard_accounts = []
    for row in acct_rows:
        balance = (row.initial_balance or 0) + row.income_sum - row.expense_sum
        dashboard_accounts.append(
            DashboardAccount(
                id=row.id,
                name=row.name,
                balance=float(balance),
                bank=row.type,
            )
        )

    # 2. Monthly Summary (Last 6 months)
    today = date.today()
    start_date = today - timedelta(days=180)

    # Incomes
    inc_month_expr = func.to_char(incomes.c.issue_date, literal("Mon"))
    inc_sort_expr = func.to_char(incomes.c.issue_date, literal("YYYY-MM"))

    inc_month = (
        select(
            inc_month_expr.label("month"),
            inc_sort_expr.label("sort_key"),
            func.sum(incomes.c.amount).label("amount"),
        )
        .where(
            incomes.c.issue_date >= start_date,
            incomes.c.active == True,
            incomes.c.issue_date.isnot(None),
        )
        .group_by(
            inc_month_expr,
            inc_sort_expr,
        )
    )

    # Expenses
    exp_month_expr = func.to_char(expenses.c.issue_date, literal("Mon"))
    exp_sort_expr = func.to_char(expenses.c.issue_date, literal("YYYY-MM"))

    exp_month = (
        select(
            exp_month_expr.label("month"),
            exp_sort_expr.label("sort_key"),
            func.sum(expenses.c.amount).label("amount"),
        )
        .where(
            expenses.c.issue_date >= start_date,
            expenses.c.active == True,
            expenses.c.issue_date.isnot(None),
        )
        .group_by(
            exp_month_expr,
            exp_sort_expr,
        )
    )

    inc_rows = session.execute(inc_month).all()
    exp_rows = session.execute(exp_month).all()

    summary_dict = {}

    for row in inc_rows:
        k = row.sort_key
        if k not in summary_dict:
            summary_dict[k] = {"month": row.month, "income": 0, "expense": 0}
        summary_dict[k]["income"] = float(row.amount)

    for row in exp_rows:
        k = row.sort_key
        if k not in summary_dict:
            summary_dict[k] = {"month": row.month, "income": 0, "expense": 0}
        summary_dict[k]["expense"] = float(row.amount)

    sorted_keys = sorted(summary_dict.keys())
    monthly_summary = [
        MonthlySummary(
            month=summary_dict[k]["month"],
            income=summary_dict[k]["income"],
            expense=summary_dict[k]["expense"],
        )
        for k in sorted_keys
    ]

    # 3. Recent Transactions
    q_inc = select(
        incomes.c.id,
        incomes.c.description,
        incomes.c.amount,
        incomes.c.issue_date.label("date"),
        literal("income").label("type"),
    ).where(incomes.c.active == True)

    q_exp = select(
        expenses.c.id,
        expenses.c.description,
        (expenses.c.amount * -1).label("amount"),
        expenses.c.issue_date.label("date"),
        literal("expense").label("type"),
    ).where(expenses.c.active == True)

    u = union_all(q_inc, q_exp).subquery()

    stmt_recent = select(u).order_by(u.c.date.desc().nulls_last()).limit(10)

    recent_rows = session.execute(stmt_recent).all()

    recent_transactions = [
        RecentTransaction(
            id=row.id,
            description=row.description,
            amount=float(row.amount),
            date=row.date,
            type=row.type,
        )
        for row in recent_rows
    ]

    return DashboardResponse(
        accounts=dashboard_accounts,
        monthlySummary=monthly_summary,
        recentTransactions=recent_transactions,
    )
