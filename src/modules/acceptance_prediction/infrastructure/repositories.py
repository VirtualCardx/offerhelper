from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.acceptance_prediction.infrastructure.models import (
    MLGovernanceEventModel,
    MLModelVersionModel,
    MLTrainingRunModel,
)
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class MLModelVersion:
    id: str
    model_name: str
    model_version: str
    framework: str
    status: str
    artifact_uri: str
    config: dict[str, object]
    metrics: dict[str, object]


@dataclass(frozen=True)
class MLTrainingRun:
    id: str
    model_name: str
    model_version: str
    framework: str
    source: str
    status: str
    activation_mode: str
    activated: bool
    activation_reason: str
    previous_active_version: str | None
    artifact_uri: str
    manifest_path: str
    model_path: str
    sample_count: int
    acceptance_rate: str
    training_accuracy: float
    training_log_loss: float
    metrics: dict[str, object]
    created_at: datetime


@dataclass(frozen=True)
class MLGovernanceEvent:
    id: str
    model_name: str
    event_type: str
    operator: str
    approval_ticket: str | None
    risk_level: str
    status: str
    reason: str
    from_version: str | None
    to_version: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None
    metadata: dict[str, object]
    created_at: datetime


class MLModelVersionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_exists(
        self,
        *,
        model_name: str,
        model_version: str,
        framework: str = "rule-based",
        status: str = "ACTIVE",
        artifact_uri: str = "",
        config: dict[str, object] | None = None,
        metrics: dict[str, object] | None = None,
    ) -> MLModelVersion:
        stmt = select(MLModelVersionModel).where(
            MLModelVersionModel.model_name == model_name,
            MLModelVersionModel.model_version == model_version,
        )
        existing = self.session.execute(stmt).scalar_one_or_none()
        if existing is None:
            existing = MLModelVersionModel(
                id=str(uuid.uuid4()),
                model_name=model_name,
                model_version=model_version,
                framework=framework,
                status=status,
                artifact_uri=artifact_uri,
                config_json=json.dumps(config or {}),
                metrics_json=json.dumps(metrics or {}),
            )
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
        else:
            changed = False
            if existing.framework != framework:
                existing.framework = framework
                changed = True
            if existing.status != status:
                existing.status = status
                changed = True
            if existing.artifact_uri != artifact_uri:
                existing.artifact_uri = artifact_uri
                changed = True
            next_config_json = json.dumps(config or {})
            next_metrics_json = json.dumps(metrics or {})
            if existing.config_json != next_config_json:
                existing.config_json = next_config_json
                changed = True
            if existing.metrics_json != next_metrics_json:
                existing.metrics_json = next_metrics_json
                changed = True
            if changed:
                self.session.commit()
                self.session.refresh(existing)
        return self._to_domain(existing)

    def list_versions(self, *, model_name: str | None = None) -> list[MLModelVersion]:
        stmt = select(MLModelVersionModel)
        if model_name is not None:
            stmt = stmt.where(MLModelVersionModel.model_name == model_name)
        records = self.session.execute(
            stmt.order_by(MLModelVersionModel.model_name, MLModelVersionModel.model_version)
        ).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_active_version(self, *, model_name: str) -> MLModelVersion:
        stmt = select(MLModelVersionModel).where(
            MLModelVersionModel.model_name == model_name,
            MLModelVersionModel.status == "ACTIVE",
        )
        record = self.session.execute(stmt.order_by(MLModelVersionModel.created_at.desc())).scalar_one_or_none()
        if record is None:
            return self.ensure_exists(
                model_name=model_name,
                model_version="0.1.0",
                framework="rule-based",
                status="ACTIVE",
                artifact_uri="registry://baseline-offer-acceptance/0.1.0",
                config={
                    "base_probability": "0.55",
                    "offer_market_bonus": "0.12",
                    "raise_bonus": "0.10",
                    "high_score_bonus": "0.06",
                    "medium_score_bonus": "0.03",
                    "competing_offer_penalty": "0.06",
                },
                metrics={"baseline": 1.0},
            )
        return self._to_domain(record)

    def activate_version(self, *, model_name: str, model_version: str) -> MLModelVersion:
        target = self.get_by_name_and_version(model_name=model_name, model_version=model_version)
        records = self.session.execute(
            select(MLModelVersionModel).where(MLModelVersionModel.model_name == model_name)
        ).scalars().all()
        for record in records:
            record.status = "ACTIVE" if record.model_version == model_version else "INACTIVE"
        self.session.commit()
        return self.get_active_version(model_name=model_name)

    def get_by_name_and_version(self, *, model_name: str, model_version: str) -> MLModelVersion:
        stmt = select(MLModelVersionModel).where(
            MLModelVersionModel.model_name == model_name,
            MLModelVersionModel.model_version == model_version,
        )
        record = self.session.execute(stmt).scalar_one_or_none()
        if record is None:
            raise DomainValidationError(f"Model '{model_name}:{model_version}' does not exist.")
        return self._to_domain(record)

    @staticmethod
    def _to_domain(model: MLModelVersionModel) -> MLModelVersion:
        return MLModelVersion(
            id=model.id,
            model_name=model.model_name,
            model_version=model.model_version,
            framework=model.framework,
            status=model.status,
            artifact_uri=model.artifact_uri,
            config=json.loads(model.config_json),
            metrics=json.loads(model.metrics_json),
        )


class MLTrainingRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        model_name: str,
        model_version: str,
        framework: str,
        source: str,
        status: str,
        activation_mode: str,
        activated: bool,
        activation_reason: str,
        previous_active_version: str | None,
        artifact_uri: str,
        manifest_path: str,
        model_path: str,
        sample_count: int,
        acceptance_rate: str,
        training_accuracy: float,
        training_log_loss: float,
        metrics: dict[str, object] | None = None,
    ) -> MLTrainingRun:
        record = MLTrainingRunModel(
            id=str(uuid.uuid4()),
            model_name=model_name,
            model_version=model_version,
            framework=framework,
            source=source,
            status=status,
            activation_mode=activation_mode,
            activated="true" if activated else "false",
            activation_reason=activation_reason,
            previous_active_version=previous_active_version,
            artifact_uri=artifact_uri,
            manifest_path=manifest_path,
            model_path=model_path,
            sample_count=str(sample_count),
            acceptance_rate=acceptance_rate,
            training_accuracy=str(training_accuracy),
            training_log_loss=str(training_log_loss),
            metrics_json=json.dumps(metrics or {}),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def list_runs(self, *, model_name: str | None = None, limit: int = 50) -> list[MLTrainingRun]:
        stmt = select(MLTrainingRunModel)
        if model_name is not None:
            stmt = stmt.where(MLTrainingRunModel.model_name == model_name)
        records = self.session.execute(
            stmt.order_by(MLTrainingRunModel.created_at.desc()).limit(limit)
        ).scalars().all()
        return [self._to_domain(record) for record in records]

    def get_latest_activated_run(
        self,
        *,
        model_name: str,
        model_version: str | None = None,
    ) -> MLTrainingRun | None:
        stmt = select(MLTrainingRunModel).where(
            MLTrainingRunModel.model_name == model_name,
            MLTrainingRunModel.activated == "true",
        )
        if model_version is not None:
            stmt = stmt.where(MLTrainingRunModel.model_version == model_version)
        record = self.session.execute(
            stmt.order_by(MLTrainingRunModel.created_at.desc())
        ).scalars().first()
        return None if record is None else self._to_domain(record)

    @staticmethod
    def _to_domain(model: MLTrainingRunModel) -> MLTrainingRun:
        return MLTrainingRun(
            id=model.id,
            model_name=model.model_name,
            model_version=model.model_version,
            framework=model.framework,
            source=model.source,
            status=model.status,
            activation_mode=model.activation_mode,
            activated=model.activated == "true",
            activation_reason=model.activation_reason,
            previous_active_version=model.previous_active_version,
            artifact_uri=model.artifact_uri,
            manifest_path=model.manifest_path,
            model_path=model.model_path,
            sample_count=int(model.sample_count),
            acceptance_rate=model.acceptance_rate,
            training_accuracy=float(model.training_accuracy),
            training_log_loss=float(model.training_log_loss),
            metrics=json.loads(model.metrics_json),
            created_at=model.created_at,
        )


class MLGovernanceEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        model_name: str,
        event_type: str,
        operator: str,
        approval_ticket: str | None,
        risk_level: str,
        status: str,
        reason: str,
        from_version: str | None,
        to_version: str | None,
        metadata: dict[str, object] | None = None,
    ) -> MLGovernanceEvent:
        record = MLGovernanceEventModel(
            id=str(uuid.uuid4()),
            model_name=model_name,
            event_type=event_type,
            operator=operator,
            approval_ticket=approval_ticket,
            risk_level=risk_level,
            status=status,
            reason=reason,
            from_version=from_version,
            to_version=to_version,
            metadata_json=json.dumps(metadata or {}),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def get_by_id(
        self,
        *,
        event_id: str,
    ) -> MLGovernanceEvent:
        record = self.session.execute(
            select(MLGovernanceEventModel).where(MLGovernanceEventModel.id == event_id)
        ).scalar_one_or_none()
        if record is None:
            raise DomainValidationError(f"Governance event '{event_id}' does not exist.")
        return self._to_domain(record)

    def update_review(
        self,
        *,
        event_id: str,
        status: str,
        reviewer: str,
        reason: str,
        approval_ticket: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> MLGovernanceEvent:
        record = self.session.execute(
            select(MLGovernanceEventModel).where(MLGovernanceEventModel.id == event_id)
        ).scalar_one_or_none()
        if record is None:
            raise DomainValidationError(f"Governance event '{event_id}' does not exist.")
        merged_metadata = json.loads(record.metadata_json)
        merged_metadata.update(
            {
                "reviewedBy": reviewer,
                "reviewedAt": datetime.now().isoformat(),
            }
        )
        merged_metadata.update(metadata or {})
        record.status = status
        if approval_ticket is not None:
            record.approval_ticket = approval_ticket
        record.reason = reason
        record.metadata_json = json.dumps(merged_metadata)
        self.session.commit()
        self.session.refresh(record)
        return self._to_domain(record)

    def list_events(
        self,
        *,
        model_name: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        operator: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 50,
    ) -> list[MLGovernanceEvent]:
        stmt = select(MLGovernanceEventModel)
        if model_name is not None:
            stmt = stmt.where(MLGovernanceEventModel.model_name == model_name)
        if event_type is not None:
            stmt = stmt.where(MLGovernanceEventModel.event_type == event_type)
        if status is not None:
            stmt = stmt.where(MLGovernanceEventModel.status == status)
        if operator is not None:
            stmt = stmt.where(MLGovernanceEventModel.operator == operator)
        if created_after is not None:
            stmt = stmt.where(MLGovernanceEventModel.created_at >= created_after)
        if created_before is not None:
            stmt = stmt.where(MLGovernanceEventModel.created_at <= created_before)
        records = self.session.execute(
            stmt.order_by(MLGovernanceEventModel.created_at.desc()).limit(limit)
        ).scalars().all()
        return [self._to_domain(record) for record in records]

    @staticmethod
    def _to_domain(model: MLGovernanceEventModel) -> MLGovernanceEvent:
        return MLGovernanceEvent(
            id=model.id,
            model_name=model.model_name,
            event_type=model.event_type,
            operator=model.operator,
            approval_ticket=model.approval_ticket,
            risk_level=model.risk_level,
            status=model.status,
            reason=model.reason,
            from_version=model.from_version,
            to_version=model.to_version,
            reviewed_by=json.loads(model.metadata_json).get("reviewedBy"),
            reviewed_at=MLGovernanceEventRepository._parse_datetime(json.loads(model.metadata_json).get("reviewedAt")),
            metadata=json.loads(model.metadata_json),
            created_at=model.created_at,
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
