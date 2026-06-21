"""equity and reports schema

Revision ID: 20260620_0003
Revises: 20260620_0002
Create Date: 2026-06-20 00:03:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260620_0003"
down_revision = "20260620_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employee_salary",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("department_id", sa.String(length=36), sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("position_id", sa.String(length=36), sa.ForeignKey("positions.id"), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=False),
        sa.Column("salary", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_employee_salary_company_id", "employee_salary", ["company_id"])
    op.create_index("ix_employee_salary_department_id", "employee_salary", ["department_id"])
    op.create_index("ix_employee_salary_position_id", "employee_salary", ["position_id"])
    op.create_index("ix_employee_salary_level", "employee_salary", ["level"])

    op.add_column("offers", sa.Column("equity_score", sa.Integer(), nullable=False, server_default="70"))
    op.add_column("offers", sa.Column("equity_risk_level", sa.String(length=20), nullable=False, server_default="LOW"))
    op.add_column("offers", sa.Column("equity_p25", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("offers", sa.Column("equity_p50", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("offers", sa.Column("equity_p75", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("offers", sa.Column("inversion_detected", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("offers", sa.Column("equity_message", sa.Text(), nullable=False, server_default=""))

    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("offer_id", sa.String(length=36), sa.ForeignKey("offers.id"), nullable=False),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reports_offer_id", "reports", ["offer_id"])


def downgrade() -> None:
    op.drop_index("ix_reports_offer_id", table_name="reports")
    op.drop_table("reports")

    op.drop_column("offers", "equity_message")
    op.drop_column("offers", "inversion_detected")
    op.drop_column("offers", "equity_p75")
    op.drop_column("offers", "equity_p50")
    op.drop_column("offers", "equity_p25")
    op.drop_column("offers", "equity_risk_level")
    op.drop_column("offers", "equity_score")

    op.drop_index("ix_employee_salary_level", table_name="employee_salary")
    op.drop_index("ix_employee_salary_position_id", table_name="employee_salary")
    op.drop_index("ix_employee_salary_department_id", table_name="employee_salary")
    op.drop_index("ix_employee_salary_company_id", table_name="employee_salary")
    op.drop_table("employee_salary")
