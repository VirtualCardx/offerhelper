"""acceptance prediction schema

Revision ID: 20260620_0004
Revises: 20260620_0003
Create Date: 2026-06-20 00:04:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0004"
down_revision = "20260620_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_model_versions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("framework", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metrics_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ml_model_versions_model_name", "ml_model_versions", ["model_name"])
    op.create_index("ix_ml_model_versions_model_version", "ml_model_versions", ["model_version"])

    op.add_column(
        "offers",
        sa.Column("acceptance_model_version", sa.String(length=50), nullable=False, server_default="0.1.0"),
    )


def downgrade() -> None:
    op.drop_column("offers", "acceptance_model_version")
    op.drop_index("ix_ml_model_versions_model_version", table_name="ml_model_versions")
    op.drop_index("ix_ml_model_versions_model_name", table_name="ml_model_versions")
    op.drop_table("ml_model_versions")
