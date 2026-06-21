"""governance events schema

Revision ID: 20260620_0008
Revises: 20260620_0007
Create Date: 2026-06-20 00:08:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0008"
down_revision = "20260620_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ml_governance_events"):
        op.create_table(
            "ml_governance_events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("model_name", sa.String(length=100), nullable=False),
            sa.Column("event_type", sa.String(length=30), nullable=False),
            sa.Column("operator", sa.String(length=100), nullable=False),
            sa.Column("approval_ticket", sa.String(length=100), nullable=True),
            sa.Column("risk_level", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("from_version", sa.String(length=50), nullable=True),
            sa.Column("to_version", sa.String(length=50), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    existing_indexes = {index["name"] for index in inspector.get_indexes("ml_governance_events")}
    if "ix_ml_governance_events_model_name" not in existing_indexes:
        op.create_index("ix_ml_governance_events_model_name", "ml_governance_events", ["model_name"], unique=False)
    if "ix_ml_governance_events_event_type" not in existing_indexes:
        op.create_index("ix_ml_governance_events_event_type", "ml_governance_events", ["event_type"], unique=False)
    if "ix_ml_governance_events_operator" not in existing_indexes:
        op.create_index("ix_ml_governance_events_operator", "ml_governance_events", ["operator"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ml_governance_events_operator", table_name="ml_governance_events")
    op.drop_index("ix_ml_governance_events_event_type", table_name="ml_governance_events")
    op.drop_index("ix_ml_governance_events_model_name", table_name="ml_governance_events")
    op.drop_table("ml_governance_events")
