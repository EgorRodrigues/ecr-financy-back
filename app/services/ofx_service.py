import io
from typing import BinaryIO
from sqlalchemy.orm import Session
from ofxparse import OfxParser
from app.schemas.reconciliation import OFXImportResponse, OFXTransaction
from app.repositories.ofx_transaction_repository import OFXTransactionRepository

class OFXService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = OFXTransactionRepository(session)

    def parse_and_save_ofx(self, file_content: BinaryIO) -> OFXImportResponse:
        ofx = OfxParser.parse(file_content)
        account = ofx.account
        statement = account.statement
        
        # O bank_id pode estar em diferentes campos dependendo do banco
        bank_id = getattr(account, "bankid", None) or getattr(account, "routing_number", None)
        if not bank_id and hasattr(account, "institution"):
            bank_id = getattr(account.institution, "fid", None)

        saved_transactions = []
        for tx in statement.transactions:
            # Lidar com transações duplicadas
            if self.repo.get_by_fitid(tx.id):
                continue  # Pular transação se ela já existir

            transaction_schema = OFXTransaction(
                id=tx.id,
                amount=float(tx.amount),
                date=tx.date.date(),
                memo=tx.memo,
                type=tx.type,
                bank_id=bank_id,
                account_id=getattr(account, "number", None),
            )
            self.repo.create_ofx_transaction(transaction_schema)
            saved_transactions.append(transaction_schema)

        return OFXImportResponse(
            transactions=saved_transactions,
            account_id=getattr(account, "number", None),
            currency=getattr(statement, "currency", None),
            balance=float(statement.balance) if hasattr(statement, "balance") else None,
            balance_date=statement.balance_date.date()
            if hasattr(statement, "balance_date")
            else None,
        )
