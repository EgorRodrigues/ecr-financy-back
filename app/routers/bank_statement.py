from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select, cast, Text
from sqlalchemy.orm import Session

from app.db.postgres import accounts, expenses, incomes, categories
from app.dependencies import get_db
from app.schemas.bank_statement import BankStatementResponse, ExpenseStatementItem, IncomeStatementItem

router = APIRouter()


@router.get("/", response_model=BankStatementResponse)
def get_bank_statement(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    account_ids: Optional[List[UUID]] = Query(None),
    account_id: Optional[UUID] = Query(None, description="Alternative to account_ids for single account filtering"),
    accounts_param: Optional[List[UUID]] = Query(None, alias="accounts", description="Alias for account_ids, often sent by frontend"),
    session: Session = Depends(get_db),
):
    # Defaults
    if not end_date:
        end_date = date.today()
    if not start_date:
        # Default to 1 month ago ending on end_date
        start_date = end_date - timedelta(days=30)

    # Consolidate account filters
    # User might pass account_ids (plural), account_id (singular) or accounts (alias)
    target_accounts = []
    if account_ids:
        target_accounts.extend(account_ids)
    if account_id:
        target_accounts.append(account_id)
    if accounts_param:
        target_accounts.extend(accounts_param)
    
    # Remove duplicates if any
    target_accounts = list(set(target_accounts))

    # Prepare account filters
    # expenses/incomes table account column is Text.
    
    expense_account_filter = True
    income_account_filter = True
    account_id_filter = True

    if target_accounts:
        # Debug log to help identify issues
        print(f"Filtering by accounts: {target_accounts}")
        
        account_strs = [str(aid) for aid in target_accounts]
        account_id_filter = accounts.c.id.in_(target_accounts)
        expense_account_filter = expenses.c.account.in_(account_strs)
        income_account_filter = incomes.c.account.in_(account_strs)
    else:
        print("No account filter applied (returning all accounts)")

    # 1. Calculate Current Balance (Saldo Atual)
    # Formula: Initial Balance (of selected accounts) + Total Incomes (Received) - Total Expenses (Paid)
    # This covers the entire history up to now (or implies "current state").
    
    # A. Initial Balance
    stmt_initial = select(func.sum(accounts.c.initial_balance)).where(
        and_(
            accounts.c.active == True,
            account_id_filter
        )
    )
    initial_balance = session.execute(stmt_initial).scalar() or Decimal(0)

    # B. Total Incomes (Received, Active, Filtered by Account)
    # Using total_received instead of amount
    stmt_incomes_total = select(func.sum(incomes.c.total_received)).where(
        and_(
            incomes.c.active == True,
            incomes.c.status == 'recebido',
            income_account_filter
        )
    )
    total_incomes = session.execute(stmt_incomes_total).scalar() or Decimal(0)

    # C. Total Expenses (Paid, Active, Filtered by Account)
    # Using total_paid instead of amount
    stmt_expenses_total = select(func.sum(expenses.c.total_paid)).where(
        and_(
            expenses.c.active == True,
            expenses.c.status == 'pago',
            expense_account_filter
        )
    )
    total_expenses = session.execute(stmt_expenses_total).scalar() or Decimal(0)

    current_balance = float(initial_balance + total_incomes - total_expenses)

    # 2. List Transactions (Within Date Range) and Calculate Period Summary
    
    # Incomes Query
    # Use coalesce to fallback to issue_date if receipt_date is null
    # This helps if the user marked as received but didn't provide a receipt date
    income_date_col = func.coalesce(incomes.c.receipt_date, incomes.c.issue_date)
    
    # Detect dialect for UUID handling in joins
    bind = session.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    
    if is_sqlite:
        # SQLite stores UUID as 32-char hex string (without hyphens) when using Uuid type.
        # But incomes/expenses.category_id is Text with hyphens.
        # cast(categories.id, Text) returns 32-char hex in SQLite.
        # So we match by removing hyphens from the string column.
        category_join_condition_inc = cast(categories.c.id, Text) == func.replace(incomes.c.category_id, "-", "")
        category_join_condition_exp = cast(categories.c.id, Text) == func.replace(expenses.c.category_id, "-", "")
    else:
        # Postgres: cast(UUID, Text) returns string with hyphens. Matches standard UUID string.
        category_join_condition_inc = incomes.c.category_id == cast(categories.c.id, Text)
        category_join_condition_exp = expenses.c.category_id == cast(categories.c.id, Text)

    stmt_inc = select(
        incomes,
        categories.c.name.label("category_name")
    ).select_from(
        incomes.outerjoin(categories, category_join_condition_inc)
    ).where(
        and_(
            incomes.c.active == True,
            incomes.c.status == 'recebido',
            income_date_col >= start_date,
            income_date_col <= end_date,
            income_account_filter
        )
    )

    # Expenses Query (Amount positive)
    stmt_exp = select(
        expenses,
        categories.c.name.label("category_name")
    ).select_from(
        expenses.outerjoin(categories, category_join_condition_exp)
    ).where(
        and_(
            expenses.c.active == True,
            expenses.c.status == 'pago',
            expenses.c.payment_date >= start_date,
            expenses.c.payment_date <= end_date,
            expense_account_filter
        )
    )

    rows_inc = session.execute(stmt_inc).all()
    rows_exp = session.execute(stmt_exp).all()
    
    transactions = []
    period_income = Decimal(0)
    period_expense = Decimal(0)

    for row in rows_inc:
        row_dict = row._mapping
        amount_val = row_dict.get('total_received') or Decimal(0)
        period_income += amount_val
        
        # Pydantic will ignore extra fields from the row if not in the model
        transactions.append(IncomeStatementItem(**row_dict))
             
    for row in rows_exp:
        row_dict = row._mapping
        amount_val = row_dict.get('total_paid') or Decimal(0)
        period_expense += amount_val
        
        transactions.append(ExpenseStatementItem(**row_dict))

    # Sort transactions by date descending
    def get_sort_date(item):
        if isinstance(item, IncomeStatementItem):
            return item.receipt_date or item.issue_date or date.min
        elif isinstance(item, ExpenseStatementItem):
            return item.payment_date or date.min
        return date.min

    transactions.sort(key=get_sort_date, reverse=True)

    return BankStatementResponse(
        account_balance=current_balance,
        period_summary={
            "total_income": float(period_income),
            "total_expense": float(period_expense),
            "net_result": float(period_income - period_expense)
        },
        transactions=transactions
    )
