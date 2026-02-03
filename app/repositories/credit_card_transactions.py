from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select, cast, Text
from sqlalchemy.orm import Session

from app.models.accounts import Account
from app.models.credit_card_transactions import CreditCardTransaction
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
    query = select(CreditCardTransaction).where(
        CreditCardTransaction.account == str(account_id),
    )

    rows = session.scalars(query).all()

    transactions_out = [CreditCardTransactionOut.model_validate(row) for row in rows]

    total_spent = sum(t.amount for t in transactions_out if t.status != "cancelado")
    available_limit = total_limit - total_spent

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
    
    # Normalize account to ensure consistency
    if transaction_data.get("account"):
        try:
            transaction_data["account"] = str(UUID(str(transaction_data["account"])))
        except ValueError:
            pass  # Leave as is if not a valid UUID

    # Convert other UUID fields to strings if they are present
    for field in ["category_id", "subcategory_id", "cost_center_id", "contact_id"]:
        if transaction_data.get(field):
            transaction_data[field] = str(transaction_data[field])

    # Invoice Logic
    invoice_id = None
    if transaction_data.get("account") and transaction_data.get("due_date"):
        # Assuming account is UUID string
        try:
            account_uuid = UUID(str(transaction_data["account"]))
            invoice = ensure_invoice_for_transaction(session, account_uuid, transaction_data["due_date"])
            invoice_id = invoice.id

            if transaction_data.get("status") != "cancelado":
                update_invoice_amount(session, invoice.id, transaction_data["amount"])
        except Exception:
            pass
            
    transaction_data["id"] = eid
    transaction_data["created_at"] = now
    transaction_data["updated_at"] = now
    transaction_data["invoice_id"] = invoice_id
    
    # Remove computed fields or fields not in model if any (none expected based on schema)
    
    new_transaction = CreditCardTransaction(**transaction_data)
    session.add(new_transaction)
    session.flush()
    session.refresh(new_transaction)
    
    return CreditCardTransactionOut.model_validate(new_transaction)


def list_credit_card_transactions(
    session: Session, limit: int = 50, account: str | None = None, account_type: str | None = None
) -> list[CreditCardTransactionOut]:
    query = select(CreditCardTransaction)

    if account:
        query = query.where(CreditCardTransaction.account == account)

    if account_type:
        query = query.join(
            Account, CreditCardTransaction.account == cast(Account.id, Text)
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
    if data.account:
        try:
            data.account = str(UUID(str(data.account)))
        except ValueError:
            pass

    # Prepare new values (using current as fallback for logic)
    new_amount = data.amount if data.amount is not None else current.amount
    new_status = data.status if data.status is not None else current.status
    new_issue_date = data.issue_date if data.issue_date is not None else current.issue_date
    new_due_date = data.due_date if data.due_date is not None else current.due_date
    new_account = data.account if data.account is not None else current.account

    # Determine new invoice
    new_invoice_id = current.invoice_id
    recalc_invoice = False

    # Check triggers for invoice recalculation
    # If due_date changed, OR issue_date changed (and no due_date), OR account changed
    if (
        (data.due_date is not None and data.due_date != current.due_date)
        or (
            data.issue_date is not None
            and data.issue_date != current.issue_date
            and new_due_date is None
        )
        or (data.account is not None and str(data.account) != str(current.account))
    ):
        recalc_invoice = True

    if recalc_invoice and new_account and new_issue_date is not None:
        try:
            account_uuid = UUID(str(new_account))
            new_invoice = ensure_invoice_for_transaction(session, account_uuid, new_issue_date)
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
    has_changes = False
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Convert UUID fields to strings
    for field in ["category_id", "subcategory_id", "cost_center_id", "contact_id", "account"]:
        if field in update_data and update_data[field]:
            update_data[field] = str(update_data[field])

    for key, value in update_data.items():
        if hasattr(current, key) and getattr(current, key) != value:
            setattr(current, key, value)
            has_changes = True

    if new_invoice_id != current.invoice_id:
        current.invoice_id = new_invoice_id
        has_changes = True

    if has_changes:
        current.updated_at = datetime.now(UTC)
        session.add(current)
        session.flush()
        session.refresh(current)

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
    session.flush()
    return True
