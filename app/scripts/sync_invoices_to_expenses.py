from uuid import uuid4
from sqlalchemy import select, insert, func
from app.core.config import settings
from app.db.postgres import connect_postgres, close_postgres, credit_card_invoices, expenses, accounts

def main() -> None:
    print("Starting sync of invoices to expenses...")
    SessionLocal = connect_postgres(settings)
    session = SessionLocal()
    
    try:
        # 1. Get all invoices
        stmt = select(credit_card_invoices)
        invoices = session.execute(stmt).all()
        print(f"Found {len(invoices)} invoices total.")
        
        synced_count = 0
        skipped_count = 0
        
        for invoice in invoices:
            # 2. Check if expense exists
            expense_query = select(expenses).where(expenses.c.invoice_id == invoice.id)
            existing_expense = session.execute(expense_query).first()
            
            if existing_expense:
                skipped_count += 1
                continue
                
            # 3. Create Expense
            # Get Account Name
            account_name_query = select(accounts.c.name).where(accounts.c.id == invoice.account_id)
            account_name = session.execute(account_name_query).scalar_one_or_none() or "Unknown Account"

            expense_status = "pago" if invoice.status == "paid" else "pendente"
            description = f"Fatura Cartão - {account_name} - {invoice.due_date.strftime('%m/%Y')}"

            session.execute(
                insert(expenses).values(
                    id=uuid4(),
                    invoice_id=invoice.id,
                    amount=invoice.amount,
                    status=expense_status,
                    due_date=invoice.due_date,
                    description=description,
                    account=account_name,
                    active=True,
                    created_at=func.now(),
                    updated_at=func.now()
                )
            )
            synced_count += 1
            print(f"Synced invoice {invoice.id} (Due: {invoice.due_date})")
            
        session.commit()
        print(f"Sync complete. Created {synced_count} expenses. Skipped {skipped_count} existing.")
        
    except Exception as e:
        session.rollback()
        print(f"Error during sync: {e}")
    finally:
        close_postgres(session)

if __name__ == "__main__":
    main()
