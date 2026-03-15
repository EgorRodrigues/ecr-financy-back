from sqlalchemy import Boolean, Column, String, Float, Date, Integer, UniqueConstraint
from app.db.base import Base

class OFXTransaction(Base):
    __tablename__ = 'ofx_transactions'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fitid = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    memo = Column(String)
    type = Column(String)
    bank_id = Column(String)
    account_id = Column(String)
    reconciled = Column(Boolean, default=False)
    active = Column(Boolean, default=True, nullable=False)
    reconciliation_date = Column(Date, nullable=True)
    reconciled_by = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('fitid', 'bank_id', 'account_id', name='_fitid_bank_account_uc'),
    )
