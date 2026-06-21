"""offer outcome schema

Revision ID: 20260620_0006
Revises: 20260620_0005
Create Date: 2026-06-20 00:06:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0006"
down_revision = "20260620_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "offers",
        sa.Column("outcome_status", sa.String(length=20), nullable=False, server_default="PENDING"),
    )
    op.add_column(
        "offers",
        sa.Column("outcome_notes", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "offers",
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_offers_outcome_status", "offers", ["outcome_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_offers_outcome_status", table_name="offers")
    op.drop_column("offers", "decided_at")
    op.drop_column("offers", "outcome_notes")
    op.drop_column("offers", "outcome_status")
