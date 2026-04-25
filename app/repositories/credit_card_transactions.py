from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select, cast, Text
from sqlalchemy.orm import Session

from app.models.accounts import Account
from app.models.credit_card_transactions import CreditCardTransaction
from app.models.credit_card_invoices import CreditCardInvoice
from app.schemas.credit_card_transactions import (
    CreditCardSummary,
    CreditCardTransactionCreate,
    CreditCardTransactionOut,
    CreditCardTransactionUpdate,
)
from app.repositories.credit_card_invoices import (
    ensure_invoice_for_transaction,
    get_account_invoices_summary,
    update_invoice_amount,
)

UTC = timezone.utc


def _to_date(value):
    return value.date() if hasattr(value, "date") else value


def get_credit_card_summary(session: Session, account_id: UUID) -> CreditCardSummary | None:
    # 1. Get Account details to find the limit
    account = session.get(Account, account_id)

    if not account:
        return None

    total_limit = (
        account.available_limit if account.available_limit is not None else Decimal("0")
    )

    # 2. Get all transactions for this account (excluding cancelled)
    # The 'account' column in CreditCardTransaction is a string (Text)
    # Wait, it's actually account_id and it is UUID.
    query = select(CreditCardTransaction).where(
        CreditCardTransaction.account_id == account_id,
    )

    rows = session.scalars(query).all()

    transactions_out = [CreditCardTransactionOut.model_validate(row) for row in rows]

    # Calculate used limit based on Open/Closed Invoices (not Paid)
    # User requested: available_limit = total_limit - sum(invoices where status != 'paid')
    stmt_invoices = select(func.sum(CreditCardInvoice.amount)).where(
        CreditCardInvoice.account_id == account_id,
        CreditCardInvoice.status != "paid"
    )
    used_limit = session.scalar(stmt_invoices) or Decimal("0")
    
    available_limit = total_limit - used_limit

    current_invoice, next_invoices = get_account_invoices_summary(session, account_id)

    return CreditCardSummary(
        total_limit=total_limit,
        available_limit=available_limit,
        transactions=transactions_out,
        current_invoice=current_invoice,
        next_invoices=next_invoices,
    )


def create_credit_card_transaction(
    session: Session, data: CreditCardTransactionCreate
) -> CreditCardTransactionOut:
    eid = uuid4()
    now = datetime.now(UTC)

    transaction_data = data.model_dump()
    
    # Invoice Logic
    invoice_id = None
    if transaction_data.get("account_id") and transaction_data.get("due_date"):
        try:
            account_uuid = transaction_data["account_id"]
            invoice = ensure_invoice_for_transaction(session, account_uuid, transaction_data["due_date"])
            invoice_id = invoice.id

            if transaction_data.get("status") != "cancelado":
                update_invoice_amount(session, invoice.id, transaction_data["amount"])
        except Exception as e:
            # Log the error but don't fail the transaction creation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to create/update invoice for transaction: {e}")
            session.rollback()
            invoice_id = None
            
    transaction_data["id"] = eid
    transaction_data["created_at"] = now
    transaction_data["updated_at"] = now
    transaction_data["invoice_id"] = invoice_id
    
    # Remove computed fields or fields not in model if any (none expected based on schema)
    
    new_transaction = CreditCardTransaction(**transaction_data)
    session.add(new_transaction)
    session.commit()
    
    return CreditCardTransactionOut.model_validate(new_transaction)


def list_credit_card_transactions(
    session: Session, limit: int = 50, account_id: UUID | None = None, account_type: str | None = None
) -> list[CreditCardTransactionOut]:
    query = select(CreditCardTransaction)

    if account_id:
        query = query.where(CreditCardTransaction.account_id == account_id)

    if account_type:
        query = query.join(
            Account, CreditCardTransaction.account_id == Account.id
        )
        query = query.where(Account.type == account_type)

    query = query.order_by(CreditCardTransaction.created_at.desc())

    rows = session.scalars(query.limit(limit)).all()
    return [CreditCardTransactionOut.model_validate(row) for row in rows]


def get_credit_card_transaction(session: Session, eid: UUID) -> CreditCardTransactionOut | None:
    row = session.get(CreditCardTransaction, eid)
    if not row:
        return None
    return CreditCardTransactionOut.model_validate(row)


def update_credit_card_transaction(
    session: Session, eid: UUID, data: CreditCardTransactionUpdate
) -> CreditCardTransactionOut | None:
    current = session.get(CreditCardTransaction, eid)
    if not current:
        return None

    # Helper to check if value changed
    def value_changed(old, new):
        return new is not None and new != old

    # Normalize account in update data
    update_dict = data.model_dump(exclude_unset=True)
    
    if "account" in update_dict:
        update_dict["account_id"] = update_dict.pop("account")
    
    # Prepare new values (using current as fallback for logic)
    new_amount = update_dict.get("amount", current.amount)
    new_status = update_dict.get("status", current.status)
    new_issue_date = update_dict.get("issue_date", current.issue_date)
    new_due_date = update_dict.get("due_date", current.due_date)
    new_account_id = update_dict.get("account_id", current.account_id)

    # Determine new invoice
    new_invoice_id = current.invoice_id
    recalc_invoice = False

    # Check triggers for invoice recalculation
    # Only recalculate invoice if account changes. Date changes should NOT trigger invoice change.
    if "account_id" in update_dict and new_account_id != current.account_id:
        recalc_invoice = True

    if recalc_invoice and new_account_id and new_issue_date is not None:
        try:
            new_invoice = ensure_invoice_for_transaction(session, new_account_id, new_issue_date)
            new_invoice_id = new_invoice.id
        except Exception:
            pass

    # Handle Invoice Amount Update
    if new_invoice_id == current.invoice_id:
        if current.invoice_id:
            delta = Decimal("0")

            # Scenario 1: Status Changed to 'cancelado' (Remove amount)
            if current.status != "cancelado" and new_status == "cancelado":
                delta -= Decimal(str(current.amount))

            # Scenario 2: Status Changed from 'cancelado' to active (Add amount)
            elif current.status == "cancelado" and new_status != "cancelado":
                delta += Decimal(str(new_amount))

            # Scenario 3: Amount changed, and neither is 'cancelado'
            elif current.status != "cancelado" and new_status != "cancelado":
                delta += Decimal(str(new_amount)) - Decimal(str(current.amount))

            if delta != Decimal("0"):
                update_invoice_amount(session, current.invoice_id, delta)
    else:
        # Invoice Changed
        # Remove from old
        if current.invoice_id and current.status != "cancelado":
            update_invoice_amount(session, current.invoice_id, -Decimal(str(current.amount)))

        # Add to new
        if new_invoice_id and new_status != "cancelado":
            update_invoice_amount(session, new_invoice_id, Decimal(str(new_amount)))

    # Apply updates to current object
    for key, value in update_dict.items():
        setattr(current, key, value)

    if new_invoice_id != current.invoice_id:
        current.invoice_id = new_invoice_id

    current.updated_at = datetime.now(UTC)
    session.add(current)
    session.commit()
    return CreditCardTransactionOut.model_validate(current)


def transfer_transaction_invoice(
    session: Session, transaction_id: UUID, new_invoice_id: UUID
) -> CreditCardTransactionOut | None:
    current = session.get(CreditCardTransaction, transaction_id)
    if not current:
        return None

    new_invoice = session.get(CreditCardInvoice, new_invoice_id)
    if not new_invoice:
        raise ValueError("Target invoice not found")

    if current.invoice_id == new_invoice_id:
        return CreditCardTransactionOut.model_validate(current)

    # 1. Deduct from old invoice (if active)
    if current.invoice_id and current.status != "cancelado":
        update_invoice_amount(session, current.invoice_id, -Decimal(str(current.amount)))

    # 2. Add to new invoice (if active)
    if current.status != "cancelado":
        update_invoice_amount(session, new_invoice_id, Decimal(str(current.amount)))

    # 3. Update transaction
    current.invoice_id = new_invoice_id
    current.updated_at = datetime.now(UTC)

    session.add(current)
    session.commit()

    return CreditCardTransactionOut.model_validate(current)


def delete_credit_card_transaction(session: Session, eid: UUID) -> bool:
    # Handle Invoice Amount?
    # If deleting a non-cancelled transaction, we should decrease invoice amount.
    current = session.get(CreditCardTransaction, eid)
    if not current:
        return False
        
    if current.invoice_id and current.status != "cancelado":
        update_invoice_amount(session, current.invoice_id, -Decimal(str(current.amount)))

    session.delete(current)
    session.commit()
    return True
