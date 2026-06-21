"""strategy and offer schema

Revision ID: 20260620_0002
Revises: 20260620_0001
Create Date: 2026-06-20 00:02:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0002"
down_revision = "20260620_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compensation_strategies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("budget_policy_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_compensation_strategies_company_id", "compensation_strategies", ["company_id"])

    op.create_table(
        "compensation_strategy_factors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "strategy_id",
            sa.String(length=36),
            sa.ForeignKey("compensation_strategies.id"),
            nullable=False,
        ),
        sa.Column("factor_code", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Numeric(8, 4), nullable=False),
        sa.Column("min_value", sa.Numeric(8, 4), nullable=False),
        sa.Column("target_value", sa.Numeric(8, 4), nullable=False),
        sa.Column("max_value", sa.Numeric(8, 4), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_compensation_strategy_factors_strategy_id",
        "compensation_strategy_factors",
        ["strategy_id"],
    )

    op.create_table(
        "offers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column(
            "strategy_id",
            sa.String(length=36),
            sa.ForeignKey("compensation_strategies.id"),
            nullable=False,
        ),
        sa.Column("recommended_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("range_min", sa.Numeric(12, 2), nullable=False),
        sa.Column("range_max", sa.Numeric(12, 2), nullable=False),
        sa.Column("cr_value", sa.Numeric(8, 4), nullable=False),
        sa.Column("accept_probability", sa.Numeric(8, 4), nullable=False),
        sa.Column("competitiveness_score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(8, 4), nullable=False),
        sa.Column("budget_usage_ratio", sa.Numeric(8, 4), nullable=False),
        sa.Column("budget_risk_level", sa.String(length=20), nullable=False),
        sa.Column("overall_risk_level", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_offers_candidate_id", "offers", ["candidate_id"])
    op.create_index("ix_offers_strategy_id", "offers", ["strategy_id"])

    op.create_table(
        "offer_risk_assessments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("offer_id", sa.String(length=36), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("reasons", sa.Text(), nullable=False),
    )
    op.create_index("ix_offer_risk_assessments_offer_id", "offer_risk_assessments", ["offer_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_offer_risk_assessments_offer_id", table_name="offer_risk_assessments")
    op.drop_table("offer_risk_assessments")
    op.drop_index("ix_offers_strategy_id", table_name="offers")
    op.drop_index("ix_offers_candidate_id", table_name="offers")
    op.drop_table("offers")
    op.drop_index(
        "ix_compensation_strategy_factors_strategy_id",
        table_name="compensation_strategy_factors",
    )
    op.drop_table("compensation_strategy_factors")
    op.drop_index("ix_compensation_strategies_company_id", table_name="compensation_strategies")
    op.drop_table("compensation_strategies")
