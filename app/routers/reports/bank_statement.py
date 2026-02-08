from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Text, and_, cast, func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.accounts import Account
from app.models.categories import Category
from app.models.expenses import Expense
from app.models.incomes import Income
from app.schemas.bank_statement import (
    BankStatementResponse,
    ExpenseStatementItem,
    IncomeStatementItem,
)

router = APIRouter()


@router.get("/", response_model=BankStatementResponse)
def get_bank_statement(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    account_ids: list[UUID] | None = Query(None),
    account_id: UUID | None = Query(
        None, description="Alternative to account_ids for single account filtering"
    ),
    accounts_param: list[UUID] | None = Query(
        None, alias="accounts", description="Alias for account_ids, often sent by frontend"
    ),
    session: Session = Depends(get_db),
):
    # Defaults
    if not end_date:
        end_date = date.today()
    if not start_date:
        # Default to 1 month ago ending on end_date
        start_date = end_date - timedelta(days=30)

    # Consolidate account filters
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
    # expenses/incomes table account column is UUID.

    expense_account_filter = True
    income_account_filter = True
    account_id_filter = True

    if target_accounts:
        # Debug log to help identify issues
        print(f"Filtering by accounts: {target_accounts}")

        account_id_filter = Account.id.in_(target_accounts)
        expense_account_filter = Expense.account.in_(target_accounts)
        income_account_filter = Income.account.in_(target_accounts)
    else:
        print("No account filter applied (returning all accounts)")

    # 1. Calculate Current Balance (Saldo Atual)
    # A. Initial Balance
    stmt_initial = select(func.sum(Account.initial_balance)).where(
        and_(Account.active == True, account_id_filter)
    )
    initial_balance = session.execute(stmt_initial).scalar() or Decimal(0)

    # B. Total Incomes
    stmt_incomes_total = select(func.sum(Income.total_received)).where(
        and_(Income.active == True, Income.status == "recebido", income_account_filter)
    )
    total_incomes = session.execute(stmt_incomes_total).scalar() or Decimal(0)

    # C. Total Expenses
    stmt_expenses_total = select(func.sum(Expense.total_paid)).where(
        and_(Expense.active == True, Expense.status == "pago", expense_account_filter)
    )
    total_expenses = session.execute(stmt_expenses_total).scalar() or Decimal(0)

    current_balance = float(initial_balance + total_incomes - total_expenses)

    # 2. List Transactions (Within Date Range) and Calculate Period Summary

    # Incomes Query
    income_date_col = func.coalesce(Income.receipt_date, Income.issue_date)

    # Detect dialect for UUID handling in joins
    bind = session.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    if is_sqlite:
        category_join_condition_inc = cast(Category.id, Text) == func.replace(
            Income.category_id, "-", ""
        )
        category_join_condition_exp = cast(Category.id, Text) == func.replace(
            Expense.category_id, "-", ""
        )
    else:
        category_join_condition_inc = Income.category_id == cast(Category.id, Text)
        category_join_condition_exp = Expense.category_id == cast(Category.id, Text)

    stmt_inc = (
        select(Income, Category.name.label("category_name"))
        .outerjoin(Category, category_join_condition_inc)
        .where(
            and_(
                Income.active == True,
                Income.status == "recebido",
                income_date_col >= start_date,
                income_date_col <= end_date,
                income_account_filter,
            )
        )
    )

    # Expenses Query
    stmt_exp = (
        select(Expense, Category.name.label("category_name"))
        .outerjoin(Category, category_join_condition_exp)
        .where(
            and_(
                Expense.active == True,
                Expense.status == "pago",
                Expense.payment_date >= start_date,
                Expense.payment_date <= end_date,
                expense_account_filter,
            )
        )
    )

    rows_inc = session.execute(stmt_inc).all()
    rows_exp = session.execute(stmt_exp).all()

    transactions = []
    period_income = Decimal(0)
    period_expense = Decimal(0)

    for row in rows_inc:
        income_obj = row.Income
        category_name = row.category_name
        
        amount_val = income_obj.total_received or Decimal(0)
        period_income += amount_val

        # Convert ORM object to dict and add category_name
        item_data = income_obj.__dict__.copy()
        item_data["category_name"] = category_name
        # Filter out SQLAlchemy state
        if "_sa_instance_state" in item_data:
            del item_data["_sa_instance_state"]
            
        transactions.append(IncomeStatementItem(**item_data))

    for row in rows_exp:
        expense_obj = row.Expense
        category_name = row.category_name
        
        amount_val = expense_obj.total_paid or Decimal(0)
        period_expense += amount_val

        item_data = expense_obj.__dict__.copy()
        item_data["category_name"] = category_name
        if "_sa_instance_state" in item_data:
            del item_data["_sa_instance_state"]

        transactions.append(ExpenseStatementItem(**item_data))

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
            "net_result": float(period_income - period_expense),
        },
        transactions=transactions,
    )
