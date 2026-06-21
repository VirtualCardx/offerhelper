"""governance review schema

Revision ID: 20260620_0009
Revises: 20260620_0008
Create Date: 2026-06-20 00:09:00
"""

from __future__ import annotations

revision = "20260620_0009"
down_revision = "20260620_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Review metadata is stored in metadata_json to stay compatible with existing local databases.
    pass


def downgrade() -> None:
    pass
