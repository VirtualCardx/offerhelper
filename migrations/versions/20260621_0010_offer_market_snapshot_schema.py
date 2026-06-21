"""offer market snapshot schema

Revision ID: 20260621_0010
Revises: 20260620_0009
Create Date: 2026-06-21 10:10:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260621_0010"
down_revision = "20260620_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("offers", sa.Column("market_snapshot_id", sa.String(length=36), nullable=True))
    op.create_index("ix_offers_market_snapshot_id", "offers", ["market_snapshot_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_offers_market_snapshot_id", table_name="offers")
    op.drop_column("offers", "market_snapshot_id")
