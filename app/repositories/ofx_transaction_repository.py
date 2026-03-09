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

    def create_ofx_transaction(self, transaction: OFXTransactionSchema) -> OFXTransaction:
        db_transaction = OFXTransaction(
            fitid=transaction.id,  # Mapeando o 'id' do schema para 'fitid' no modelo
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