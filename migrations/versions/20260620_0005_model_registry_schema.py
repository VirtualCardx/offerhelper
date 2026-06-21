"""model registry schema

Revision ID: 20260620_0005
Revises: 20260620_0004
Create Date: 2026-06-20 00:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0005"
down_revision = "20260620_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ml_model_versions",
        sa.Column("artifact_uri", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "ml_model_versions",
        sa.Column("config_json", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("ml_model_versions", "config_json")
    op.drop_column("ml_model_versions", "artifact_uri")
