"""add expense installment groups and installment fields

Revision ID: 202604300001
Revises: 202604280001
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202604300001"
down_revision: Union[str, None] = "202604280001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expense_installment_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("amount_total", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("installments_total", sa.Integer(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("first_due_date", sa.Date(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column("expenses", sa.Column("installment_group_id", sa.UUID(), nullable=True))
    op.add_column("expenses", sa.Column("installment_number", sa.Integer(), nullable=True))
    op.add_column("expenses", sa.Column("installments_total", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_expenses_installment_group_id"),
        "expenses",
        ["installment_group_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_installment_group_id"), table_name="expenses")
    op.drop_column("expenses", "installments_total")
    op.drop_column("expenses", "installment_number")
    op.drop_column("expenses", "installment_group_id")
    op.drop_table("expense_installment_groups")
