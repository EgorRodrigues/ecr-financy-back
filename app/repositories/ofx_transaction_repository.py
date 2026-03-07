from sqlalchemy.orm import Session
from app.models.ofx_transaction import OFXTransaction
from app.schemas.reconciliation import OFXTransaction as OFXTransactionSchema

class OFXTransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_fitid(self, fitid: str) -> OFXTransaction | None:
        return self.session.query(OFXTransaction).filter(OFXTransaction.fitid == fitid).first()

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