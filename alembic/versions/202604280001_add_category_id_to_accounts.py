"""add category_id to accounts

Revision ID: 202604280001
Revises: 202603150001
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "202604280001"
down_revision: Union[str, None] = "202603150001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("category_id", sa.UUID(), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "category_id")

