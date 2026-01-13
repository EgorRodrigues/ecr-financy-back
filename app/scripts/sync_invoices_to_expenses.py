from uuid import uuid4
from sqlalchemy import select, insert, update, func
from app.core.config import settings
from app.db.postgres import (
    connect_postgres,
    close_postgres,
    credit_card_invoices,
    credit_card_transactions,
    expenses,
    accounts,
)


def main() -> None:
    print("Starting sync of invoices to expenses (Invoice -> Expense Model)...")
    SessionLocal = connect_postgres(settings)
    session = SessionLocal()

    try:
        # 1. Get all invoices
        stmt = select(credit_card_invoices)
        invoices = session.execute(stmt).all()
        print(f"Found {len(invoices)} invoices total.")

        synced_count = 0
        skipped_count = 0
        linked_existing_count = 0
        corrected_amount_count = 0

        for invoice in invoices:
            # 1.1 Recalculate Invoice Amount based on Transactions
            sum_stmt = select(func.sum(credit_card_transactions.c.amount)).where(
                credit_card_transactions.c.invoice_id == invoice.id,
                credit_card_transactions.c.active,
            )
            calculated_amount = session.execute(sum_stmt).scalar() or 0

            # Use calculated_amount for logic, and update DB if different
            current_invoice_amount = invoice.amount

            if calculated_amount != invoice.amount:
                print(
                    f"Correcting invoice {invoice.id} amount from {invoice.amount} to {calculated_amount}"
                )
                session.execute(
                    update(credit_card_invoices)
                    .where(credit_card_invoices.c.id == invoice.id)
                    .values(amount=calculated_amount)
                )
                current_invoice_amount = calculated_amount
                corrected_amount_count += 1

            # 2. Check if expense exists (linked in invoice)
            if invoice.expense_id:
                # Check if expense amount matches current_invoice_amount (Sync update)
                existing_linked_expense_query = select(expenses.c.amount).where(
                    expenses.c.id == invoice.expense_id
                )
                existing_linked_expense_amount = session.execute(
                    existing_linked_expense_query
                ).scalar()

                if (
                    existing_linked_expense_amount is not None
                    and existing_linked_expense_amount != current_invoice_amount
                ):
                    print(
                        f"Updating linked expense {invoice.expense_id} amount from {existing_linked_expense_amount} to {current_invoice_amount}"
                    )
                    session.execute(
                        update(expenses)
                        .where(expenses.c.id == invoice.expense_id)
                        .values(amount=current_invoice_amount)
                    )

                skipped_count += 1
                continue

            # 3. Prepare Expense Data
            # Get Account Name
            account_name_query = select(accounts.c.name).where(accounts.c.id == invoice.account_id)
            account_name = (
                session.execute(account_name_query).scalar_one_or_none() or "Unknown Account"
            )

            expense_status = "pago" if invoice.status == "paid" else "pendente"
            description = f"Fatura Cartão - {account_name} - {invoice.due_date.strftime('%m/%Y')}"

            # 4. Check for existing orphan expense (Heuristic match)
            # Since we removed invoice_id from expenses, we match by data to avoid duplicates
            existing_expense_query = select(expenses).where(
                expenses.c.amount == current_invoice_amount,
                expenses.c.due_date == invoice.due_date,
                expenses.c.description == description,
            )
            existing_expense = session.execute(existing_expense_query).first()

            if existing_expense:
                expense_id = existing_expense.id
                print(f"Found existing orphan expense {expense_id} for invoice {invoice.id}")
                linked_existing_count += 1
            else:
                # 5. Create new Expense
                expense_id = uuid4()
                session.execute(
                    insert(expenses).values(
                        id=expense_id,
                        amount=current_invoice_amount,
                        status=expense_status,
                        due_date=invoice.due_date,
                        description=description,
                        account=account_name,
                        active=True,
                        created_at=func.now(),
                        updated_at=func.now(),
                    )
                )
                synced_count += 1

            # 6. Update Invoice with expense_id
            session.execute(
                update(credit_card_invoices)
                .where(credit_card_invoices.c.id == invoice.id)
                .values(expense_id=expense_id)
            )

            if not existing_expense:
                print(f"Synced invoice {invoice.id} (Created Expense: {expense_id})")

        session.commit()
        print(
            f"Sync complete. Created {synced_count} expenses. Linked {linked_existing_count} existing. Skipped {skipped_count} already linked. Corrected Amounts: {corrected_amount_count}"
        )

    except Exception as e:
        session.rollback()
        print(f"Error during sync: {e}")
    finally:
        close_postgres(session)


if __name__ == "__main__":
    main()
