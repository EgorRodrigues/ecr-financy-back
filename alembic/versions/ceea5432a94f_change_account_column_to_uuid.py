"""change_account_column_to_uuid

Revision ID: ceea5432a94f
Revises: 2ab4ae9d61ad
Create Date: 2026-02-07 23:16:43.034188
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ceea5432a94f'
down_revision: Union[str, None] = '2ab4ae9d61ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Data Fix: Update account names to account IDs (UUIDs)
    # This matches expenses.account (text) with accounts.name and replaces it with accounts.id
    op.execute("""
        UPDATE expenses
        SET account = accounts.id::text
        FROM accounts
        WHERE expenses.account = accounts.name
    """)
    
    op.execute("""
        UPDATE incomes
        SET account = accounts.id::text
        FROM accounts
        WHERE incomes.account = accounts.name
    """)

    # 2. Change columns to UUID
    # Change expenses.account to UUID
    op.execute('ALTER TABLE expenses ALTER COLUMN account TYPE UUID USING account::uuid')
    # Change incomes.account to UUID
    op.execute('ALTER TABLE incomes ALTER COLUMN account TYPE UUID USING account::uuid')


def downgrade() -> None:
    # Revert expenses.account to TEXT
    op.execute('ALTER TABLE expenses ALTER COLUMN account TYPE TEXT')
    # Revert incomes.account to TEXT
    op.execute('ALTER TABLE incomes ALTER COLUMN account TYPE TEXT')
    
    # Note: We cannot easily revert UUIDs back to names without a reverse lookup logic, 
    # and we probably don't want to since UUIDs are the correct reference.
