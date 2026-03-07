import io
from typing import BinaryIO

from ofxparse import OfxParser

from app.schemas.reconciliation import OFXImportResponse, OFXTransaction


class OFXService:
    @staticmethod
    def parse_ofx(file_content: BinaryIO) -> OFXImportResponse:
        ofx = OfxParser.parse(file_content)
        account = ofx.account
        statement = account.statement

        transactions = []
        for tx in statement.transactions:
            transactions.append(
                OFXTransaction(
                    id=tx.id,
                    amount=float(tx.amount),
                    date=tx.date.date(),
                    memo=tx.memo,
                    type=tx.type,
                    bank_id=getattr(account, "bankid", None),
                    account_id=getattr(account, "number", None),
                )
            )

        return OFXImportResponse(
            transactions=transactions,
            account_id=getattr(account, "number", None),
            currency=getattr(statement, "currency", None),
            balance=float(statement.balance) if hasattr(statement, "balance") else None,
            balance_date=statement.balance_date.date()
            if hasattr(statement, "balance_date")
            else None,
        )
