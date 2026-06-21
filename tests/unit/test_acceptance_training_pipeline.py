from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.modules.acceptance_prediction.application.training_pipeline import AcceptanceModelTrainingPipeline
from src.modules.acceptance_prediction.application.governance import ModelGovernanceService
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.config.settings import get_settings
from src.shared.infrastructure.db.base import Base
from src.shared.presentation.errors import DomainValidationError


def test_training_pipeline_registers_and_activates_model(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        result = AcceptanceModelTrainingPipeline(
            session,
            output_dir=Path(tmp_path),
        ).run(
            model_name="baseline-offer-acceptance",
            model_version="pipeline-test-0.1.0",
            framework="xgboost",
            source="demo",
            activation_mode="always",
        )

        active_model = MLModelVersionRepository(session).get_active_version(model_name="baseline-offer-acceptance")
        training_runs = MLTrainingRunRepository(session).list_runs(model_name="baseline-offer-acceptance")
        governance_events = MLGovernanceEventRepository(session).list_events(model_name="baseline-offer-acceptance")

    Base.metadata.drop_all(bind=engine)

    assert result.model_version == "pipeline-test-0.1.0"
    assert result.registered_model.status == "ACTIVE"
    assert result.artifact_uri.endswith("pipeline-test-0.1.0.json")
    assert active_model.model_version == "pipeline-test-0.1.0"
    assert active_model.framework == "xgboost"
    assert result.activation_reason == "Activation mode is set to always."
    assert len(training_runs) == 1
    assert training_runs[0].model_version == "pipeline-test-0.1.0"
    assert training_runs[0].activated is True
    assert len(governance_events) == 1
    assert governance_events[0].event_type == "TRAIN"
    assert governance_events[0].operator == "system"


def test_training_pipeline_generates_next_version_and_keeps_inactive_when_not_better(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        repository = MLModelVersionRepository(session)
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.8.0",
            framework="xgboost",
            status="ACTIVE",
            artifact_uri="file:///tmp/0.8.0.json",
            config={},
            metrics={
                "trainingAccuracy": 1.0,
                "trainingLogLoss": 0.0001,
            },
        )
        result = AcceptanceModelTrainingPipeline(
            session,
            output_dir=Path(tmp_path),
        ).run(
            model_name="baseline-offer-acceptance",
            model_version=None,
            framework="xgboost",
            source="demo",
            activation_mode="if_better",
        )

        active_model = MLModelVersionRepository(session).get_active_version(model_name="baseline-offer-acceptance")
        trained_model = MLModelVersionRepository(session).get_by_name_and_version(
            model_name="baseline-offer-acceptance",
            model_version=result.model_version,
        )

    Base.metadata.drop_all(bind=engine)

    assert result.model_version == "0.8.1"
    assert result.activated is False
    assert result.previous_active_version == "0.8.0"
    assert result.activation_reason == "New model does not outperform the active model based on training metrics."
    assert active_model.model_version == "0.8.0"
    assert trained_model.status == "INACTIVE"


def test_governance_rolls_back_to_previous_activated_version(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        repository = MLModelVersionRepository(session)
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.8.0",
            framework="xgboost",
            status="ACTIVE",
            artifact_uri="file:///tmp/0.8.0.json",
            config={},
            metrics={"trainingAccuracy": 0.8, "trainingLogLoss": 0.2},
        )
        AcceptanceModelTrainingPipeline(
            session,
            output_dir=Path(tmp_path),
        ).run(
            model_name="baseline-offer-acceptance",
            model_version="0.8.1",
            framework="xgboost",
            source="demo",
            activation_mode="always",
        )

        rollback = ModelGovernanceService(
            version_repository=repository,
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        ).rollback_active_model(model_name="baseline-offer-acceptance")
        active_model = repository.get_active_version(model_name="baseline-offer-acceptance")

    Base.metadata.drop_all(bind=engine)

    assert rollback.from_version == "0.8.1"
    assert rollback.to_version == "0.8.0"
    assert rollback.reason == "Rollback target resolved from latest activation snapshot."
    assert active_model.model_version == "0.8.0"


def test_high_risk_rollback_requires_approval_ticket(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        repository = MLModelVersionRepository(session)
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.7.0",
            framework="xgboost",
            status="ACTIVE",
            artifact_uri="file:///tmp/0.7.0.json",
            config={},
            metrics={"trainingAccuracy": 0.8, "trainingLogLoss": 0.2},
        )
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.1.0",
            framework="rule-based",
            status="INACTIVE",
            artifact_uri="registry://baseline-offer-acceptance/0.1.0",
            config={},
            metrics={},
        )
        governance_service = ModelGovernanceService(
            version_repository=repository,
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        )

        pending = governance_service.rollback_active_model(
            model_name="baseline-offer-acceptance",
            target_version="0.1.0",
            operator="auditor",
        )
        active_before_review = repository.get_active_version(model_name="baseline-offer-acceptance")
        reviewed = governance_service.review_governance_event(
            event_id=pending.governance_event_id,
            reviewer="approver",
            action="APPROVE",
            comment="Approved for emergency rollback.",
            approval_ticket="APR-001",
        )
        events = MLGovernanceEventRepository(session).list_events(
            model_name="baseline-offer-acceptance",
            event_type="ROLLBACK",
        )
        active_after_review = repository.get_active_version(model_name="baseline-offer-acceptance")

    Base.metadata.drop_all(bind=engine)

    assert pending.risk_level == "HIGH"
    assert pending.status == "PENDING"
    assert pending.executed is False
    assert pending.to_version == "0.1.0"
    assert active_before_review.model_version == "0.7.0"
    assert reviewed.status == "APPROVED"
    assert reviewed.executed is True
    assert len(events) == 1
    assert events[0].approval_ticket == "APR-001"
    assert events[0].risk_level == "HIGH"
    assert events[0].status == "APPROVED"
    assert events[0].reviewed_by == "approver"
    assert active_after_review.model_version == "0.1.0"


def test_review_can_reject_pending_high_risk_rollback(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        repository = MLModelVersionRepository(session)
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.9.0",
            framework="xgboost",
            status="ACTIVE",
            artifact_uri="file:///tmp/0.9.0.json",
            config={},
            metrics={"trainingAccuracy": 0.9, "trainingLogLoss": 0.1},
        )
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.1.0",
            framework="rule-based",
            status="INACTIVE",
            artifact_uri="registry://baseline-offer-acceptance/0.1.0",
            config={},
            metrics={},
        )
        governance_service = ModelGovernanceService(
            version_repository=repository,
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        )
        pending = governance_service.rollback_active_model(
            model_name="baseline-offer-acceptance",
            target_version="0.1.0",
            operator="auditor",
        )
        reviewed = governance_service.review_governance_event(
            event_id=pending.governance_event_id,
            reviewer="approver",
            action="REJECT",
            comment="Rollback rejected after review.",
        )
        active_model = repository.get_active_version(model_name="baseline-offer-acceptance")

    Base.metadata.drop_all(bind=engine)

    assert pending.status == "PENDING"
    assert reviewed.status == "REJECTED"
    assert reviewed.executed is False
    assert active_model.model_version == "0.9.0"


def test_approve_pending_high_risk_rollback_requires_approval_ticket(tmp_path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        repository = MLModelVersionRepository(session)
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.9.0",
            framework="xgboost",
            status="ACTIVE",
            artifact_uri="file:///tmp/0.9.0.json",
            config={},
            metrics={"trainingAccuracy": 0.9, "trainingLogLoss": 0.1},
        )
        repository.ensure_exists(
            model_name="baseline-offer-acceptance",
            model_version="0.1.0",
            framework="rule-based",
            status="INACTIVE",
            artifact_uri="registry://baseline-offer-acceptance/0.1.0",
            config={},
            metrics={},
        )
        governance_service = ModelGovernanceService(
            version_repository=repository,
            training_run_repository=MLTrainingRunRepository(session),
            governance_event_repository=MLGovernanceEventRepository(session),
        )
        pending = governance_service.rollback_active_model(
            model_name="baseline-offer-acceptance",
            target_version="0.1.0",
            operator="auditor",
        )

        with pytest.raises(
            DomainValidationError,
            match="Approval ticket is required when approving a pending rollback event.",
        ):
            governance_service.review_governance_event(
                event_id=pending.governance_event_id,
                reviewer="approver",
                action="APPROVE",
                comment="Attempted approval without ticket.",
            )

        active_model = repository.get_active_version(model_name="baseline-offer-acceptance")
        event = MLGovernanceEventRepository(session).get_by_id(event_id=pending.governance_event_id)

    Base.metadata.drop_all(bind=engine)

    assert pending.status == "PENDING"
    assert active_model.model_version == "0.9.0"
    assert event.status == "PENDING"


def test_expire_pending_high_risk_rollback_blocks_late_review(tmp_path) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    settings.governance_pending_review_ttl_hours = 0

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    try:
        with SessionLocal() as session:
            repository = MLModelVersionRepository(session)
            repository.ensure_exists(
                model_name="baseline-offer-acceptance",
                model_version="0.9.0",
                framework="xgboost",
                status="ACTIVE",
                artifact_uri="file:///tmp/0.9.0.json",
                config={},
                metrics={"trainingAccuracy": 0.9, "trainingLogLoss": 0.1},
            )
            repository.ensure_exists(
                model_name="baseline-offer-acceptance",
                model_version="0.1.0",
                framework="rule-based",
                status="INACTIVE",
                artifact_uri="registry://baseline-offer-acceptance/0.1.0",
                config={},
                metrics={},
            )
            governance_service = ModelGovernanceService(
                version_repository=repository,
                training_run_repository=MLTrainingRunRepository(session),
                governance_event_repository=MLGovernanceEventRepository(session),
            )
            pending = governance_service.rollback_active_model(
                model_name="baseline-offer-acceptance",
                target_version="0.1.0",
                operator="auditor",
            )
            expiration = governance_service.expire_pending_governance_events(
                model_name="baseline-offer-acceptance",
                operator="governance-bot",
            )

            with pytest.raises(
                DomainValidationError,
                match="Governance event '.*' is not pending review.|expired before review.",
            ):
                governance_service.review_governance_event(
                    event_id=pending.governance_event_id,
                    reviewer="approver",
                    action="APPROVE",
                    comment="Too late approval.",
                    approval_ticket="APR-LATE",
                )

            event = MLGovernanceEventRepository(session).get_by_id(event_id=pending.governance_event_id)
            active_model = repository.get_active_version(model_name="baseline-offer-acceptance")

        assert expiration.expired_count == 1
        assert expiration.expired_event_ids == [pending.governance_event_id]
        assert event.status == "EXPIRED"
        assert event.metadata["expired"] is True
        assert event.metadata["expiresAt"]
        assert active_model.model_version == "0.9.0"
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours
        Base.metadata.drop_all(bind=engine)
