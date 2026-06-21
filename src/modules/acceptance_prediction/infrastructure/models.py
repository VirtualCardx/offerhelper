from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MLModelVersionModel(Base):
    __tablename__ = "ml_model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False, default="rule-based")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE")
    artifact_uri: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class MLTrainingRunModel(Base):
    __tablename__ = "ml_training_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False, default="rule-based")
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="db")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="COMPLETED")
    activation_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="if_better")
    activated: Mapped[str] = mapped_column(String(5), nullable=False, default="false")
    activation_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    previous_active_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    artifact_uri: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    manifest_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    model_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sample_count: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    acceptance_rate: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    training_accuracy: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    training_log_loss: Mapped[str] = mapped_column(String(20), nullable=False, default="0")
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class MLGovernanceEventModel(Base):
    __tablename__ = "ml_governance_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    operator: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="system")
    approval_ticket: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SUCCESS")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    from_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
