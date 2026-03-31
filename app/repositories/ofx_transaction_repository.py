from datetime import date
from sqlalchemy.orm import Session
from app.models.ofx_transaction import OFXTransaction
from app.schemas.reconciliation import OFXTransaction as OFXTransactionSchema

class OFXTransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_existing_transaction(self, fitid: str, bank_id: str | None, account_id: str | None) -> OFXTransaction | None:
        query = self.session.query(OFXTransaction).filter(OFXTransaction.fitid == fitid)
        if bank_id:
            query = query.filter(OFXTransaction.bank_id == bank_id)
        if account_id:
            query = query.filter(OFXTransaction.account_id == account_id)
        return query.first()

    def get_unreconciled_active(self, start_date: date | None = None, end_date: date | None = None) -> list[OFXTransaction]:
        query = self.session.query(OFXTransaction).filter(
            OFXTransaction.reconciled == False,
            OFXTransaction.active == True
        )

        if start_date:
            query = query.filter(OFXTransaction.date >= start_date)

        if end_date:
            query = query.filter(OFXTransaction.date <= end_date)

        return query.all()

    def get_by_ids_active(self, ids: list[int]) -> list[OFXTransaction]:
        return self.session.query(OFXTransaction).filter(
            OFXTransaction.id.in_(ids),
            OFXTransaction.active == True
        ).all()

    def deactivate(self, transaction_id: int) -> OFXTransaction | None:
        transaction = self.session.query(OFXTransaction).filter(OFXTransaction.id == transaction_id).first()
        if transaction:
            transaction.active = False
            self.session.commit()
            self.session.refresh(transaction)
        return transaction

    def create_ofx_transaction(self, transaction: OFXTransactionSchema) -> OFXTransaction:
        db_transaction = OFXTransaction(
            fitid=transaction.fitid,  # Agora usando explicitamente fitid
            amount=transaction.amount,
            date=transaction.date,
            memo=transaction.memo,
            type=transaction.type,
            bank_id=transaction.bank_id,
            account_id=transaction.account_id
        )
        self.session.add(db_transaction)
        self.session.commit()
        self.session.refresh(db_transaction)
        return db_transaction