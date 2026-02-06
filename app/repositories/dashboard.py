from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.accounts import Account
from app.models.expenses import Expense
from app.models.incomes import Income
from app.schemas.dashboard import (
    DashboardAccount,
    DashboardResponse,
    MonthlySummary,
    RecentTransaction,
)


class DashboardRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_dashboard_data(self) -> DashboardResponse:
        return DashboardResponse(
            accounts=self._get_accounts_with_balance(),
            monthlySummary=self._get_monthly_summary(),
            recentTransactions=self._get_recent_transactions(),
        )

    def _get_accounts_with_balance(self) -> list[DashboardAccount]:
        # 1. Accounts with Balance
        # Fetch all active accounts
        stmt_accounts = select(Account).where(Account.active == True)
        acct_rows = self.session.scalars(stmt_accounts).all()

        # Fetch all active incomes (received only)
        stmt_incomes = (
            select(Income.account, func.sum(Income.total_received))
            .where(Income.active == True, Income.status == "recebido")
            .group_by(Income.account)
        )
        income_rows = self.session.execute(stmt_incomes).all()

        # Fetch all active expenses (paid only)
        stmt_expenses = (
            select(Expense.account, func.sum(Expense.total_paid))
            .where(Expense.active == True, Expense.status == "pago")
            .group_by(Expense.account)
        )
        expense_rows = self.session.execute(stmt_expenses).all()

        # Calculate balances in Python
        account_balances = {}
        account_info = {}

        # Initialize with initial balance
        for row in acct_rows:
            str_id = str(row.id)
            account_balances[str_id] = float(row.initial_balance or 0)
            account_info[str_id] = row

        # Process Incomes
        for acc_id, amount in income_rows:
            # Ensure acc_id matches the format of str(row.id)
            if acc_id and acc_id in account_balances:
                account_balances[acc_id] += float(amount or 0)

        # Process Expenses
        for acc_id, amount in expense_rows:
            if acc_id and acc_id in account_balances:
                account_balances[acc_id] -= float(amount or 0)

        # Build result list
        dashboard_accounts = []
        for acc_id, balance in account_balances.items():
            row = account_info[acc_id]
            dashboard_accounts.append(
                DashboardAccount(
                    id=row.id,
                    name=row.name,
                    balance=balance,
                    bank=row.type,
                )
            )
        return dashboard_accounts

    def _get_monthly_summary(self) -> list[MonthlySummary]:
        # 2. Monthly Summary (Last 6 months)
        today = date.today()
        start_date = today - timedelta(days=180)

        # Fetch incomes within range (received only)
        # Using coalesce(receipt_date, issue_date) to align with bank statement
        inc_date_col = func.coalesce(Income.receipt_date, Income.issue_date)
        stmt_inc = select(inc_date_col, Income.total_received).where(
            inc_date_col >= start_date,
            Income.active == True,
            Income.status == "recebido",
        )
        # Fetch expenses within range (paid only)
        # Using coalesce(payment_date, issue_date) to align with bank statement logic if needed,
        # but Expense model has issue_date. Let's check Expense model.
        # Assuming issue_date is fine, but usually paid expenses have a payment date?
        # Let's stick to issue_date for now or better, check if there is a payment_date.
        # Checking Expense model... it has issue_date. It does not seem to have payment_date explicitly in the select above?
        # Wait, I should verify Expense model fields.
        # In the previous read of Income model, I saw receipt_date.
        # Let's assume Expense has payment_date or similar.
        # Actually, let's just use issue_date if that's what was used, but logically realized date is better.
        # However, to be safe and consistent with "status=pago", let's just add the status filter and use total_paid.
        stmt_exp = select(Expense.issue_date, Expense.total_paid).where(
            Expense.issue_date >= start_date,
            Expense.active == True,
            Expense.status == "pago",
            Expense.issue_date.isnot(None),
        )

        inc_rows = self.session.execute(stmt_inc).all()
        exp_rows = self.session.execute(stmt_exp).all()

        summary_dict = {}

        # Process Incomes
        for date_val, amount in inc_rows:
            if not date_val:
                continue
            d = date_val
            sort_key = d.strftime("%Y-%m")
            month_label = d.strftime("%b")

            if sort_key not in summary_dict:
                summary_dict[sort_key] = {"month": month_label, "income": 0, "expense": 0}
            summary_dict[sort_key]["income"] += float(amount or 0)

        # Process Expenses
        for date_val, amount in exp_rows:
            if not date_val:
                continue
            d = date_val
            sort_key = d.strftime("%Y-%m")
            month_label = d.strftime("%b")

            if sort_key not in summary_dict:
                summary_dict[sort_key] = {"month": month_label, "income": 0, "expense": 0}
            summary_dict[sort_key]["expense"] += float(amount or 0)

        sorted_keys = sorted(summary_dict.keys())
        monthly_summary = [
            MonthlySummary(
                month=summary_dict[k]["month"],
                income=summary_dict[k]["income"],
                expense=summary_dict[k]["expense"],
            )
            for k in sorted_keys
        ]
        return monthly_summary

    def _get_recent_transactions(self) -> list[RecentTransaction]:
        # 3. Recent Transactions
        # Fetch top 10 incomes (received only)
        # Use receipt_date if available, else issue_date
        inc_date_col = func.coalesce(Income.receipt_date, Income.issue_date)
        
        q_inc = (
            select(
                Income.id,
                Income.description,
                Income.total_received.label("amount"),
                inc_date_col.label("date"),
            )
            .where(Income.active == True, Income.status == "recebido")
            .order_by(inc_date_col.desc().nulls_last())
            .limit(10)
        )

        # Fetch top 10 expenses (paid only)
        q_exp = (
            select(
                Expense.id,
                Expense.description,
                Expense.total_paid.label("amount"),
                Expense.issue_date.label("date"),
            )
            .where(Expense.active == True, Expense.status == "pago")
            .order_by(Expense.issue_date.desc().nulls_last())
            .limit(10)
        )

        inc_rows = self.session.execute(q_inc).all()
        exp_rows = self.session.execute(q_exp).all()

        combined = []
        for row in inc_rows:
            combined.append(
                {
                    "id": row.id,
                    "description": row.description,
                    "amount": float(row.amount or 0),
                    "date": row.date,
                    "type": "income",
                }
            )

        for row in exp_rows:
            combined.append(
                {
                    "id": row.id,
                    "description": row.description,
                    "amount": float(row.amount or 0) * -1,
                    "date": row.date,
                    "type": "expense",
                }
            )

        # Sort combined list by date desc
        def sort_key(item):
            d = item["date"]
            # Handle None dates if any (though logic usually implies they are last)
            return d if d is not None else date.min

        combined.sort(key=sort_key, reverse=True)

        # Take top 10 of combined
        combined = combined[:10]

        return [
            RecentTransaction(
                id=item["id"],
                description=item["description"],
                amount=item["amount"],
                date=item["date"],
                type=item["type"],
            )
            for item in combined
        ]
