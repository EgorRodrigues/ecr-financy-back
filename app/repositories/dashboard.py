from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.postgres import accounts, expenses, incomes
from app.models.dashboard import (
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
        stmt_accounts = select(
            accounts.c.id,
            accounts.c.name,
            accounts.c.initial_balance,
            accounts.c.type,
        ).where(accounts.c.active == True)
        acct_rows = self.session.execute(stmt_accounts).all()

        # Fetch all active incomes
        stmt_incomes = select(incomes.c.account, incomes.c.amount).where(
            incomes.c.active == True
        )
        income_rows = self.session.execute(stmt_incomes).all()

        # Fetch all active expenses
        stmt_expenses = select(expenses.c.account, expenses.c.amount).where(
            expenses.c.active == True
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
        for row in income_rows:
            acc_id = row.account
            # Ensure acc_id matches the format of str(row.id)
            if acc_id and acc_id in account_balances:
                account_balances[acc_id] += float(row.amount or 0)

        # Process Expenses
        for row in expense_rows:
            acc_id = row.account
            if acc_id and acc_id in account_balances:
                account_balances[acc_id] -= float(row.amount or 0)

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

        # Fetch incomes within range
        stmt_inc = select(incomes.c.issue_date, incomes.c.amount).where(
            incomes.c.issue_date >= start_date,
            incomes.c.active == True,
            incomes.c.issue_date.isnot(None),
        )
        # Fetch expenses within range
        stmt_exp = select(expenses.c.issue_date, expenses.c.amount).where(
            expenses.c.issue_date >= start_date,
            expenses.c.active == True,
            expenses.c.issue_date.isnot(None),
        )

        inc_rows = self.session.execute(stmt_inc).all()
        exp_rows = self.session.execute(stmt_exp).all()

        summary_dict = {}

        # Process Incomes
        for row in inc_rows:
            d = row.issue_date
            sort_key = d.strftime("%Y-%m")
            month_label = d.strftime("%b")

            if sort_key not in summary_dict:
                summary_dict[sort_key] = {"month": month_label, "income": 0, "expense": 0}
            summary_dict[sort_key]["income"] += float(row.amount)

        # Process Expenses
        for row in exp_rows:
            d = row.issue_date
            sort_key = d.strftime("%Y-%m")
            month_label = d.strftime("%b")

            if sort_key not in summary_dict:
                summary_dict[sort_key] = {"month": month_label, "income": 0, "expense": 0}
            summary_dict[sort_key]["expense"] += float(row.amount)

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
        # Fetch top 10 incomes
        q_inc = (
            select(
                incomes.c.id,
                incomes.c.description,
                incomes.c.amount,
                incomes.c.issue_date.label("date"),
            )
            .where(incomes.c.active == True)
            .order_by(incomes.c.issue_date.desc().nulls_last())
            .limit(10)
        )

        # Fetch top 10 expenses
        q_exp = (
            select(
                expenses.c.id,
                expenses.c.description,
                expenses.c.amount,
                expenses.c.issue_date.label("date"),
            )
            .where(expenses.c.active == True)
            .order_by(expenses.c.issue_date.desc().nulls_last())
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
                    "amount": float(row.amount),
                    "date": row.date,
                    "type": "income",
                }
            )

        for row in exp_rows:
            combined.append(
                {
                    "id": row.id,
                    "description": row.description,
                    "amount": float(row.amount) * -1,
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

        # Take top 10
        top_10 = combined[:10]

        return [RecentTransaction(**item) for item in top_10]
