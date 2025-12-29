from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, insert, update, delete, func, Text
from app.models.credit_card_transactions import (
    CreditCardTransactionCreate,
    CreditCardTransactionUpdate,
    CreditCardTransactionOut,
    CreditCardSummary,
)
from app.db.postgres import credit_card_transactions, accounts
from app.repositories.credit_card_invoices import (
    ensure_invoice_for_transaction,
    update_invoice_amount,
    get_account_invoices_summary,
)


def _to_date(value):
    return value.date() if hasattr(value, "date") else value


def get_credit_card_summary(session, account_id: UUID) -> CreditCardSummary | None:
    # 1. Get Account details to find the limit
    account_row = session.execute(
        select(accounts.c.available_limit).where(accounts.c.id == account_id)
    ).one_or_none()

    if not account_row:
        return None

    total_limit = (
        account_row.available_limit if account_row.available_limit is not None else Decimal("0")
    )

    # 2. Get all transactions for this account (excluding cancelled)
    query = select(
        credit_card_transactions.c.id,
        credit_card_transactions.c.amount,
        credit_card_transactions.c.status,
        credit_card_transactions.c.issue_date,
        credit_card_transactions.c.due_date,
        credit_card_transactions.c.payment_date,
        credit_card_transactions.c.original_amount,
        credit_card_transactions.c.interest,
        credit_card_transactions.c.fine,
        credit_card_transactions.c.discount,
        credit_card_transactions.c.total_paid,
        credit_card_transactions.c.category_id,
        credit_card_transactions.c.subcategory_id,
        credit_card_transactions.c.cost_center_id,
        credit_card_transactions.c.contact_id,
        credit_card_transactions.c.description,
        credit_card_transactions.c.document,
        credit_card_transactions.c.payment_method,
        credit_card_transactions.c.account,
        credit_card_transactions.c.recurrence,
        credit_card_transactions.c.competence,
        credit_card_transactions.c.project,
        credit_card_transactions.c.tags,
        credit_card_transactions.c.notes,
        credit_card_transactions.c.active,
        credit_card_transactions.c.invoice_id,
        credit_card_transactions.c.created_at,
        credit_card_transactions.c.updated_at,
    ).where(
        credit_card_transactions.c.account == str(account_id),
        credit_card_transactions.c.status != "cancelado",
    )

    rows = session.execute(query).all()

    transactions_out = [
        CreditCardTransactionOut(
            id=row.id,
            amount=row.amount if row.amount is not None else Decimal("0"),
            status=row.status,
            issue_date=_to_date(row.issue_date),
            due_date=_to_date(row.due_date),
            payment_date=_to_date(row.payment_date),
            original_amount=row.original_amount,
            interest=row.interest,
            fine=row.fine,
            discount=row.discount,
            total_paid=row.total_paid,
            category_id=row.category_id,
            subcategory_id=row.subcategory_id,
            cost_center_id=row.cost_center_id,
            contact_id=row.contact_id,
            description=row.description,
            document=row.document,
            payment_method=row.payment_method,
            account=row.account,
            recurrence=row.recurrence,
            competence=row.competence,
            project=row.project,
            tags=row.tags,
            notes=row.notes,
            active=row.active,
            invoice_id=row.invoice_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]

    total_spent = sum(t.amount for t in transactions_out)
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
    session, data: CreditCardTransactionCreate
) -> CreditCardTransactionOut:
    eid = uuid4()
    now = datetime.now(timezone.utc)

    # Invoice Logic
    invoice_id = None
    if data.account and data.due_date:
        # Assuming account is UUID string
        try:
            account_uuid = UUID(str(data.account))
            invoice = ensure_invoice_for_transaction(session, account_uuid, data.due_date)
            invoice_id = invoice.id

            if data.status != "cancelado":
                update_invoice_amount(session, invoice.id, data.amount)
        except Exception:
            # Fallback if account not found or other issue?
            # For now let it raise or ignore?
            # Ideally we want this to work.
            pass

    session.execute(
        insert(credit_card_transactions).values(
            id=eid,
            amount=data.amount,
            status=data.status,
            issue_date=data.issue_date,
            due_date=data.due_date,
            payment_date=data.payment_date,
            original_amount=data.original_amount,
            interest=data.interest,
            fine=data.fine,
            discount=data.discount,
            total_paid=data.total_paid,
            category_id=data.category_id,
            subcategory_id=data.subcategory_id,
            cost_center_id=data.cost_center_id,
            contact_id=data.contact_id,
            description=data.description,
            document=data.document,
            payment_method=data.payment_method,
            account=data.account,
            recurrence=data.recurrence,
            competence=data.competence,
            project=data.project,
            tags=data.tags,
            notes=data.notes,
            active=data.active,
            invoice_id=invoice_id,
            created_at=now,
            updated_at=now,
        )
    )
    session.commit()
    return CreditCardTransactionOut(
        id=eid,
        amount=data.amount,
        status=data.status,
        issue_date=data.issue_date,
        due_date=data.due_date,
        payment_date=data.payment_date,
        original_amount=data.original_amount,
        interest=data.interest,
        fine=data.fine,
        discount=data.discount,
        total_paid=data.total_paid,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        cost_center_id=data.cost_center_id,
        contact_id=data.contact_id,
        description=data.description,
        document=data.document,
        payment_method=data.payment_method,
        account=data.account,
        recurrence=data.recurrence,
        competence=data.competence,
        project=data.project,
        tags=data.tags,
        notes=data.notes,
        active=data.active,
        invoice_id=invoice_id,
        created_at=now,
        updated_at=now,
    )


def list_credit_card_transactions(
    session, limit: int = 50, account: str | None = None, account_type: str | None = None
) -> list[CreditCardTransactionOut]:
    query = select(
        credit_card_transactions.c.id,
        credit_card_transactions.c.amount,
        credit_card_transactions.c.status,
        credit_card_transactions.c.issue_date,
        credit_card_transactions.c.due_date,
        credit_card_transactions.c.payment_date,
        credit_card_transactions.c.original_amount,
        credit_card_transactions.c.interest,
        credit_card_transactions.c.fine,
        credit_card_transactions.c.discount,
        credit_card_transactions.c.total_paid,
        credit_card_transactions.c.category_id,
        credit_card_transactions.c.subcategory_id,
        credit_card_transactions.c.cost_center_id,
        credit_card_transactions.c.contact_id,
        credit_card_transactions.c.description,
        credit_card_transactions.c.document,
        credit_card_transactions.c.payment_method,
        credit_card_transactions.c.account,
        credit_card_transactions.c.recurrence,
        credit_card_transactions.c.competence,
        credit_card_transactions.c.project,
        credit_card_transactions.c.tags,
        credit_card_transactions.c.notes,
        credit_card_transactions.c.active,
        credit_card_transactions.c.invoice_id,
        credit_card_transactions.c.created_at,
        credit_card_transactions.c.updated_at,
    )

    if account:
        query = query.where(credit_card_transactions.c.account == account)

    if account_type:
        query = query.join(
            accounts, credit_card_transactions.c.account == func.cast(accounts.c.id, Text)
        )
        query = query.where(accounts.c.type == account_type)

    rows = session.execute(query.limit(limit)).all()
    return [
        CreditCardTransactionOut(
            id=row.id,
            amount=row.amount if row.amount is not None else Decimal("0"),
            status=row.status,
            issue_date=_to_date(row.issue_date),
            due_date=_to_date(row.due_date),
            payment_date=_to_date(row.payment_date),
            original_amount=row.original_amount,
            interest=row.interest,
            fine=row.fine,
            discount=row.discount,
            total_paid=row.total_paid,
            category_id=row.category_id,
            subcategory_id=row.subcategory_id,
            cost_center_id=row.cost_center_id,
            contact_id=row.contact_id,
            description=row.description,
            document=row.document,
            payment_method=row.payment_method,
            account=row.account,
            recurrence=row.recurrence,
            competence=row.competence,
            project=row.project,
            tags=row.tags,
            notes=row.notes,
            active=row.active,
            invoice_id=row.invoice_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def get_credit_card_transaction(session, eid: UUID) -> CreditCardTransactionOut | None:
    row = session.execute(
        select(
            credit_card_transactions.c.id,
            credit_card_transactions.c.amount,
            credit_card_transactions.c.status,
            credit_card_transactions.c.issue_date,
            credit_card_transactions.c.due_date,
            credit_card_transactions.c.payment_date,
            credit_card_transactions.c.original_amount,
            credit_card_transactions.c.interest,
            credit_card_transactions.c.fine,
            credit_card_transactions.c.discount,
            credit_card_transactions.c.total_paid,
            credit_card_transactions.c.category_id,
            credit_card_transactions.c.subcategory_id,
            credit_card_transactions.c.cost_center_id,
            credit_card_transactions.c.contact_id,
            credit_card_transactions.c.description,
            credit_card_transactions.c.document,
            credit_card_transactions.c.payment_method,
            credit_card_transactions.c.account,
            credit_card_transactions.c.recurrence,
            credit_card_transactions.c.competence,
            credit_card_transactions.c.project,
            credit_card_transactions.c.tags,
            credit_card_transactions.c.notes,
            credit_card_transactions.c.active,
            credit_card_transactions.c.invoice_id,
            credit_card_transactions.c.created_at,
            credit_card_transactions.c.updated_at,
        ).where(credit_card_transactions.c.id == eid)
    ).one_or_none()
    if not row:
        return None
    return CreditCardTransactionOut(
        id=row.id,
        amount=row.amount if row.amount is not None else Decimal("0"),
        status=row.status,
        issue_date=_to_date(row.issue_date),
        due_date=_to_date(row.due_date),
        payment_date=_to_date(row.payment_date),
        original_amount=row.original_amount,
        interest=row.interest,
        fine=row.fine,
        discount=row.discount,
        total_paid=row.total_paid,
        category_id=row.category_id,
        subcategory_id=row.subcategory_id,
        cost_center_id=row.cost_center_id,
        contact_id=row.contact_id,
        description=row.description,
        document=row.document,
        payment_method=row.payment_method,
        account=row.account,
        recurrence=row.recurrence,
        competence=row.competence,
        project=row.project,
        tags=row.tags,
        notes=row.notes,
        active=row.active,
        invoice_id=row.invoice_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_credit_card_transaction(
    session, eid: UUID, data: CreditCardTransactionUpdate
) -> CreditCardTransactionOut | None:
    current = get_credit_card_transaction(session, eid)
    if not current:
        return None

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

    if recalc_invoice and new_account:
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
                delta -= current.amount

            # Scenario 2: Status Changed from 'cancelado' to active (Add amount)
            elif current.status == "cancelado" and new_status != "cancelado":
                delta += new_amount

            # Scenario 3: Amount changed, and neither is 'cancelado'
            elif current.status != "cancelado" and new_status != "cancelado":
                delta += new_amount - current.amount

            if delta != Decimal("0"):
                update_invoice_amount(session, current.invoice_id, delta)
    else:
        # Invoice Changed
        # Remove from old
        if current.invoice_id and current.status != "cancelado":
            update_invoice_amount(session, current.invoice_id, -current.amount)

        # Add to new
        if new_invoice_id and new_status != "cancelado":
            update_invoice_amount(session, new_invoice_id, new_amount)

    new_payment_date = data.payment_date if data.payment_date is not None else current.payment_date
    new_category_id = data.category_id if data.category_id is not None else current.category_id
    new_subcategory_id = (
        data.subcategory_id if data.subcategory_id is not None else current.subcategory_id
    )
    new_cost_center_id = (
        data.cost_center_id if data.cost_center_id is not None else current.cost_center_id
    )
    new_contact_id = data.contact_id if data.contact_id is not None else current.contact_id
    new_description = data.description if data.description is not None else current.description
    new_document = data.document if data.document is not None else current.document
    new_payment_method = (
        data.payment_method if data.payment_method is not None else current.payment_method
    )
    new_recurrence = data.recurrence if data.recurrence is not None else current.recurrence
    new_competence = data.competence if data.competence is not None else current.competence
    new_project = data.project if data.project is not None else current.project
    new_tags = data.tags if data.tags is not None else current.tags
    new_notes = data.notes if data.notes is not None else current.notes
    new_active = data.active if data.active is not None else current.active
    new_original_amount = (
        data.original_amount if data.original_amount is not None else current.original_amount
    )
    new_interest = data.interest if data.interest is not None else current.interest
    new_fine = data.fine if data.fine is not None else current.fine
    new_discount = data.discount if data.discount is not None else current.discount
    new_total_paid = data.total_paid if data.total_paid is not None else current.total_paid
    now = datetime.now(timezone.utc)

    session.execute(
        update(credit_card_transactions)
        .where(credit_card_transactions.c.id == eid)
        .values(
            amount=new_amount,
            status=new_status,
            issue_date=new_issue_date,
            due_date=new_due_date,
            payment_date=new_payment_date,
            original_amount=new_original_amount,
            interest=new_interest,
            fine=new_fine,
            discount=new_discount,
            total_paid=new_total_paid,
            category_id=new_category_id,
            subcategory_id=new_subcategory_id,
            cost_center_id=new_cost_center_id,
            contact_id=new_contact_id,
            description=new_description,
            document=new_document,
            payment_method=new_payment_method,
            account=new_account,
            recurrence=new_recurrence,
            competence=new_competence,
            project=new_project,
            tags=new_tags,
            notes=new_notes,
            active=new_active,
            invoice_id=new_invoice_id,
            updated_at=now,
        )
    )
    session.commit()
    return CreditCardTransactionOut(
        id=eid,
        amount=new_amount,
        status=new_status,
        issue_date=new_issue_date,
        due_date=new_due_date,
        payment_date=new_payment_date,
        original_amount=new_original_amount,
        interest=new_interest,
        fine=new_fine,
        discount=new_discount,
        total_paid=new_total_paid,
        category_id=new_category_id,
        subcategory_id=new_subcategory_id,
        cost_center_id=new_cost_center_id,
        contact_id=new_contact_id,
        description=new_description,
        document=new_document,
        payment_method=new_payment_method,
        account=new_account,
        recurrence=new_recurrence,
        competence=new_competence,
        project=new_project,
        tags=new_tags,
        notes=new_notes,
        active=new_active,
        invoice_id=new_invoice_id,
        created_at=current.created_at,
        updated_at=now,
    )


def delete_credit_card_transaction(session, eid: UUID) -> bool:
    # Handle Invoice Amount?
    # If deleting a non-cancelled transaction, we should decrease invoice amount.
    current = get_credit_card_transaction(session, eid)
    if current and current.invoice_id and current.status != "cancelado":
        update_invoice_amount(session, current.invoice_id, -current.amount)

    session.execute(delete(credit_card_transactions).where(credit_card_transactions.c.id == eid))
    session.commit()
    return True
