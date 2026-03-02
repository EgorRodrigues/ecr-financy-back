"""make_fields_mandatory

Revision ID: d1669212865f
Revises: bd629b9cb42b
Create Date: 2026-02-25 21:32:23.018524
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd1669212865f'
down_revision: Union[str, None] = 'bd629b9cb42b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expenses
    op.alter_column('expenses', 'issue_date', existing_type=sa.Date(), nullable=False)
    op.alter_column('expenses', 'contact_id', existing_type=sa.UUID(), nullable=False)
    op.alter_column('expenses', 'description', existing_type=sa.Text(), nullable=False)
    op.alter_column('expenses', 'account_id', existing_type=sa.UUID(), nullable=False)

    # Incomes
    op.alter_column('incomes', 'issue_date', existing_type=sa.Date(), nullable=False)
    op.alter_column('incomes', 'contact_id', existing_type=sa.UUID(), nullable=False)
    op.alter_column('incomes', 'description', existing_type=sa.Text(), nullable=False)
    op.alter_column('incomes', 'account_id', existing_type=sa.UUID(), nullable=False)


def downgrade() -> None:
    # Incomes
    op.alter_column('incomes', 'account_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('incomes', 'description', existing_type=sa.Text(), nullable=True)
    op.alter_column('incomes', 'contact_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('incomes', 'issue_date', existing_type=sa.Date(), nullable=True)

    # Expenses
    op.alter_column('expenses', 'account_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('expenses', 'description', existing_type=sa.Text(), nullable=True)
    op.alter_column('expenses', 'contact_id', existing_type=sa.UUID(), nullable=True)
    op.alter_column('expenses', 'issue_date', existing_type=sa.Date(), nullable=True)

