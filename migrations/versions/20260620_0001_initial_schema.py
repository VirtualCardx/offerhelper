"""initial schema

Revision ID: 20260620_0001
Revises:
Create Date: 2026-06-20 00:01:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("industry", sa.String(length=100), nullable=False),
        sa.Column("tenant_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_departments_company_id", "departments", ["company_id"])

    op.create_table(
        "positions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("job_family", sa.String(length=100), nullable=False),
        sa.Column("level_band", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_positions_company_id", "positions", ["company_id"])

    op.create_table(
        "candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("position_id", sa.String(length=36), sa.ForeignKey("positions.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("current_salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("expected_salary", sa.Numeric(12, 2), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=False),
        sa.Column("skills", sa.Text(), nullable=False),
        sa.Column("interview_score", sa.Integer(), nullable=False),
        sa.Column("has_other_offer", sa.Boolean(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidates_company_id", "candidates", ["company_id"])
    op.create_index("ix_candidates_department_id", "candidates", ["department_id"])
    op.create_index("ix_candidates_position_id", "candidates", ["position_id"])

    op.create_table(
        "market_salary",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("position_id", sa.String(length=36), sa.ForeignKey("positions.id"), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("p25", sa.Numeric(12, 2), nullable=False),
        sa.Column("p50", sa.Numeric(12, 2), nullable=False),
        sa.Column("p75", sa.Numeric(12, 2), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_market_salary_position_id", "market_salary", ["position_id"])
    op.create_index("ix_market_salary_city", "market_salary", ["city"])
    op.create_index("ix_market_salary_update_time", "market_salary", ["update_time"])


def downgrade() -> None:
    op.drop_index("ix_market_salary_update_time", table_name="market_salary")
    op.drop_index("ix_market_salary_city", table_name="market_salary")
    op.drop_index("ix_market_salary_position_id", table_name="market_salary")
    op.drop_table("market_salary")
    op.drop_index("ix_candidates_position_id", table_name="candidates")
    op.drop_index("ix_candidates_department_id", table_name="candidates")
    op.drop_index("ix_candidates_company_id", table_name="candidates")
    op.drop_table("candidates")
    op.drop_index("ix_positions_company_id", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_departments_company_id", table_name="departments")
    op.drop_table("departments")
    op.drop_table("companies")
