from sqlalchemy import Column, String, Integer, Date, ForeignKey
from app.db.base import Base

class Reconciliation(Base):
    __tablename__ = 'reconciliations'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ofx_transaction_id = Column(Integer, ForeignKey('ofx_transactions.id'), nullable=False)
    transaction_id = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    reconciliation_date = Column(Date, nullable=False)
    reconciled_by = Column(String, nullable=False)
