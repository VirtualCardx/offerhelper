"""training audit schema

Revision ID: 20260620_0007
Revises: 20260620_0006
Create Date: 2026-06-20 00:07:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0007"
down_revision = "20260620_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ml_training_runs"):
        op.create_table(
            "ml_training_runs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("model_name", sa.String(length=100), nullable=False),
            sa.Column("model_version", sa.String(length=50), nullable=False),
            sa.Column("framework", sa.String(length=50), nullable=False),
            sa.Column("source", sa.String(length=30), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("activation_mode", sa.String(length=30), nullable=False),
            sa.Column("activated", sa.String(length=5), nullable=False),
            sa.Column("activation_reason", sa.Text(), nullable=False),
            sa.Column("previous_active_version", sa.String(length=50), nullable=True),
            sa.Column("artifact_uri", sa.String(length=255), nullable=False),
            sa.Column("manifest_path", sa.String(length=255), nullable=False),
            sa.Column("model_path", sa.String(length=255), nullable=False),
            sa.Column("sample_count", sa.String(length=20), nullable=False),
            sa.Column("acceptance_rate", sa.String(length=20), nullable=False),
            sa.Column("training_accuracy", sa.String(length=20), nullable=False),
            sa.Column("training_log_loss", sa.String(length=20), nullable=False),
            sa.Column("metrics_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    existing_indexes = {index["name"] for index in inspector.get_indexes("ml_training_runs")}
    if "ix_ml_training_runs_model_name" not in existing_indexes:
        op.create_index("ix_ml_training_runs_model_name", "ml_training_runs", ["model_name"], unique=False)
    if "ix_ml_training_runs_model_version" not in existing_indexes:
        op.create_index("ix_ml_training_runs_model_version", "ml_training_runs", ["model_version"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ml_training_runs_model_version", table_name="ml_training_runs")
    op.drop_index("ix_ml_training_runs_model_name", table_name="ml_training_runs")
    op.drop_table("ml_training_runs")
