from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.postgres import close_postgres, connect_postgres
from app.models.accounts import Account
from app.models.credit_card_invoices import CreditCardInvoice
from app.models.credit_card_transactions import CreditCardTransaction
from app.models.expenses import Expense


def main() -> None:
    print("Starting sync of invoices to expenses (Invoice -> Expense Model)...")
    SessionLocal = connect_postgres(settings)
    session = SessionLocal()

    try:
        # 1. Get all invoices
        stmt = select(CreditCardInvoice)
        invoices = session.scalars(stmt).all()
        print(f"Found {len(invoices)} invoices total.")

        synced_count = 0
        skipped_count = 0
        linked_existing_count = 0
        corrected_amount_count = 0

        for invoice in invoices:
            # 1.1 Recalculate Invoice Amount based on Transactions
            sum_stmt = select(func.sum(CreditCardTransaction.amount)).where(
                CreditCardTransaction.invoice_id == invoice.id,
                CreditCardTransaction.active == True,  # noqa: E712
            )
            calculated_amount = session.scalars(sum_stmt).first() or 0

            # Use calculated_amount for logic, and update DB if different
            current_invoice_amount = invoice.amount

            if calculated_amount != invoice.amount:
                print(
                    f"Correcting invoice {invoice.id} amount from {invoice.amount} "
                    f"to {calculated_amount}"
                )
                invoice.amount = calculated_amount
                current_invoice_amount = calculated_amount
                corrected_amount_count += 1

            # 2. Check if expense exists (linked in invoice)
            if invoice.expense_id:
                # Check if expense amount matches current_invoice_amount (Sync update)
                existing_linked_expense = session.get(Expense, invoice.expense_id)

                if (
                    existing_linked_expense
                    and existing_linked_expense.amount != current_invoice_amount
                ):
                    print(
                        f"Updating linked expense {invoice.expense_id} amount from "
                        f"{existing_linked_expense.amount} to {current_invoice_amount}"
                    )
                    existing_linked_expense.amount = current_invoice_amount

                skipped_count += 1
                continue

            # 3. Prepare Expense Data
            # Get Account Name
            account = session.get(Account, invoice.account_id)
            account_name = account.name if account else "Unknown Account"

            expense_status = "pago" if invoice.status == "paid" else "pendente"
            description = f"Fatura Cartão - {account_name} - {invoice.due_date.strftime('%m/%Y')}"

            # 4. Check for existing orphan expense (Heuristic match)
            # Since we removed invoice_id from expenses, we match by data to avoid duplicates
            existing_expense_query = select(Expense).where(
                Expense.amount == current_invoice_amount,
                Expense.due_date == invoice.due_date,
                Expense.description == description,
            )
            existing_expense = session.scalars(existing_expense_query).first()

            if existing_expense:
                expense_id = existing_expense.id
                print(f"Found existing orphan expense {expense_id} for invoice {invoice.id}")
                linked_existing_count += 1
            else:
                # 5. Create new Expense
                expense_id = uuid4()
                new_expense = Expense(
                    id=expense_id,
                    amount=current_invoice_amount,
                    status=expense_status,
                    due_date=invoice.due_date,
                    description=description,
                    account=account_name,
                    active=True,
                )
                session.add(new_expense)
                synced_count += 1

            # 6. Update Invoice with expense_id
            invoice.expense_id = expense_id

            if not existing_expense:
                print(f"Synced invoice {invoice.id} (Created Expense: {expense_id})")

        session.commit()
        print(
            f"Sync complete. Created {synced_count} expenses. "
            f"Linked {linked_existing_count} existing. "
            f"Skipped {skipped_count} already linked. "
            f"Corrected Amounts: {corrected_amount_count}"
        )

    except Exception as e:
        session.rollback()
        print(f"Error during sync: {e}")
    finally:
        close_postgres(session)


if __name__ == "__main__":
    main()
