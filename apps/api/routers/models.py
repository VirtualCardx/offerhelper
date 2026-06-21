from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.modules.acceptance_prediction.application.governance import ModelGovernanceService
from src.modules.acceptance_prediction.application.governance_notifications import GovernanceAlertNotifier
from src.modules.acceptance_prediction.application.registry import ModelRegistryService
from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.infrastructure.db.session import get_db_session


router = APIRouter(prefix="/models", tags=["Models"])


class ModelVersionResponse(BaseModel):
    id: str
    model_name: str = Field(alias="modelName")
    model_version: str = Field(alias="modelVersion")
    framework: str
    status: str
    artifact_uri: str = Field(alias="artifactUri")
    config: dict[str, object]
    metrics: dict[str, object]


class RegisterModelRequest(BaseModel):
    model_name: str = Field(alias="modelName")
    model_version: str = Field(alias="modelVersion")
    framework: str
    artifact_uri: str = Field(alias="artifactUri")
    config: dict[str, object]
    metrics: dict[str, object] = Field(default_factory=dict)
    activate: bool = False


class ActivateModelRequest(BaseModel):
    model_name: str = Field(alias="modelName")
    model_version: str = Field(alias="modelVersion")


class ValidateModelRequest(BaseModel):
    model_name: str = Field(alias="modelName")
    model_version: str = Field(alias="modelVersion")


class ModelArtifactValidationResponse(BaseModel):
    artifact_uri: str = Field(alias="artifactUri")
    framework: str
    scheme: str
    exists: bool
    loadable: bool
    resolved_path: str | None = Field(default=None, alias="resolvedPath")
    loaded_config: dict[str, object] = Field(alias="loadedConfig")
    loaded_metrics: dict[str, object] = Field(alias="loadedMetrics")
    loaded_runtime: dict[str, object] = Field(default_factory=dict, alias="loadedRuntime")


class TrainingRunResponse(BaseModel):
    id: str
    model_name: str = Field(alias="modelName")
    model_version: str = Field(alias="modelVersion")
    framework: str
    source: str
    status: str
    activation_mode: str = Field(alias="activationMode")
    activated: bool
    activation_reason: str = Field(alias="activationReason")
    previous_active_version: str | None = Field(default=None, alias="previousActiveVersion")
    artifact_uri: str = Field(alias="artifactUri")
    manifest_path: str = Field(alias="manifestPath")
    model_path: str = Field(alias="modelPath")
    sample_count: int = Field(alias="sampleCount")
    acceptance_rate: str = Field(alias="acceptanceRate")
    training_accuracy: float = Field(alias="trainingAccuracy")
    training_log_loss: float = Field(alias="trainingLogLoss")
    metrics: dict[str, object]


class RollbackModelRequest(BaseModel):
    model_name: str = Field(alias="modelName")
    target_version: str | None = Field(default=None, alias="targetVersion")
    operator: str = "system"
    approval_ticket: str | None = Field(default=None, alias="approvalTicket")


class RollbackModelResponse(BaseModel):
    model_name: str = Field(alias="modelName")
    from_version: str = Field(alias="fromVersion")
    to_version: str = Field(alias="toVersion")
    reason: str
    status: str
    risk_level: str = Field(alias="riskLevel")
    executed: bool
    governance_event_id: str = Field(alias="governanceEventId")


class GovernanceEventResponse(BaseModel):
    id: str
    model_name: str = Field(alias="modelName")
    event_type: str = Field(alias="eventType")
    operator: str
    approval_ticket: str | None = Field(default=None, alias="approvalTicket")
    risk_level: str = Field(alias="riskLevel")
    status: str
    reason: str
    from_version: str | None = Field(default=None, alias="fromVersion")
    to_version: str | None = Field(default=None, alias="toVersion")
    reviewed_by: str | None = Field(default=None, alias="reviewedBy")
    reviewed_at: datetime | None = Field(default=None, alias="reviewedAt")
    metadata: dict[str, object]
    created_at: datetime = Field(alias="createdAt")


class ReviewGovernanceEventRequest(BaseModel):
    action: str
    reviewer: str
    comment: str | None = None
    approval_ticket: str | None = Field(default=None, alias="approvalTicket")


class ReviewGovernanceEventResponse(BaseModel):
    event_id: str = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    model_name: str = Field(alias="modelName")
    status: str
    reviewer: str
    reviewed_at: datetime | None = Field(default=None, alias="reviewedAt")
    reason: str
    from_version: str | None = Field(default=None, alias="fromVersion")
    to_version: str | None = Field(default=None, alias="toVersion")
    executed: bool


class ExpirePendingGovernanceEventsRequest(BaseModel):
    model_name: str | None = Field(default=None, alias="modelName")
    pending_operator: str | None = Field(default=None, alias="pendingOperator")
    operator: str = "system"
    limit: int = Field(default=100, ge=1, le=500)


class ExpirePendingGovernanceEventsResponse(BaseModel):
    expired_count: int = Field(alias="expiredCount")
    expired_event_ids: list[str] = Field(alias="expiredEventIds")


class GovernanceAlertResponse(BaseModel):
    id: str
    event_id: str = Field(alias="eventId")
    model_name: str = Field(alias="modelName")
    event_type: str = Field(alias="eventType")
    operator: str
    status: str
    alert_type: str = Field(alias="alertType")
    severity: str
    message: str
    from_version: str | None = Field(default=None, alias="fromVersion")
    to_version: str | None = Field(default=None, alias="toVersion")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    created_at: datetime = Field(alias="createdAt")
    metadata: dict[str, object]


class GovernanceAlertNotificationRequest(BaseModel):
    model_name: str | None = Field(default=None, alias="modelName")
    operator: str | None = None
    severity: str | None = None
    alert_type: str | None = Field(default=None, alias="alertType")
    channel: Literal["log", "webhook-payload"] = "log"
    destination: str | None = None
    limit: int = Field(default=50, ge=1, le=200)


class GovernanceAlertNotificationDeliveryResponse(BaseModel):
    id: str
    alert_id: str = Field(alias="alertId")
    channel: str
    destination: str
    subject: str
    body: str
    payload: dict[str, object]


class GovernanceAlertNotificationResponse(BaseModel):
    channel: str
    destination: str
    delivery_count: int = Field(alias="deliveryCount")
    notified_alert_ids: list[str] = Field(alias="notifiedAlertIds")
    deliveries: list[GovernanceAlertNotificationDeliveryResponse]


@router.get("/versions", response_model=list[ModelVersionResponse])
async def list_model_versions(
    model_name: str | None = Query(default=None, alias="modelName"),
    session: Session = Depends(get_db_session),
) -> list[ModelVersionResponse]:
    repository = MLModelVersionRepository(session)
    registry = ModelRegistryService(repository)
    registry.ensure_default_versions()
    return [
        ModelVersionResponse(
            id=item.id,
            modelName=item.model_name,
            modelVersion=item.model_version,
            framework=item.framework,
            status=item.status,
            artifactUri=item.artifact_uri,
            config=item.config,
            metrics=item.metrics,
        )
        for item in repository.list_versions(model_name=model_name)
    ]


@router.get("/active", response_model=ModelVersionResponse)
async def get_active_model_version(
    model_name: str = Query(alias="modelName"),
    session: Session = Depends(get_db_session),
) -> ModelVersionResponse:
    repository = MLModelVersionRepository(session)
    registry = ModelRegistryService(repository)
    model = registry.get_active_model(model_name=model_name)
    return ModelVersionResponse(
        id=model.id,
        modelName=model.model_name,
        modelVersion=model.model_version,
        framework=model.framework,
        status=model.status,
        artifactUri=model.artifact_uri,
        config=model.config,
        metrics=model.metrics,
    )


@router.get("/training-runs", response_model=list[TrainingRunResponse])
async def list_training_runs(
    model_name: str | None = Query(default=None, alias="modelName"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[TrainingRunResponse]:
    repository = MLTrainingRunRepository(session)
    return [
        TrainingRunResponse(
            id=item.id,
            modelName=item.model_name,
            modelVersion=item.model_version,
            framework=item.framework,
            source=item.source,
            status=item.status,
            activationMode=item.activation_mode,
            activated=item.activated,
            activationReason=item.activation_reason,
            previousActiveVersion=item.previous_active_version,
            artifactUri=item.artifact_uri,
            manifestPath=item.manifest_path,
            modelPath=item.model_path,
            sampleCount=item.sample_count,
            acceptanceRate=item.acceptance_rate,
            trainingAccuracy=item.training_accuracy,
            trainingLogLoss=item.training_log_loss,
            metrics=item.metrics,
        )
        for item in repository.list_runs(model_name=model_name, limit=limit)
    ]


@router.get("/governance-events", response_model=list[GovernanceEventResponse])
async def list_governance_events(
    model_name: str | None = Query(default=None, alias="modelName"),
    event_type: str | None = Query(default=None, alias="eventType"),
    status: str | None = Query(default=None),
    operator: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None, alias="createdAfter"),
    created_before: datetime | None = Query(default=None, alias="createdBefore"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[GovernanceEventResponse]:
    repository = MLGovernanceEventRepository(session)
    return [
        GovernanceEventResponse(
            id=item.id,
            modelName=item.model_name,
            eventType=item.event_type,
            operator=item.operator,
            approvalTicket=item.approval_ticket,
            riskLevel=item.risk_level,
            status=item.status,
            reason=item.reason,
            fromVersion=item.from_version,
            toVersion=item.to_version,
            reviewedBy=item.reviewed_by,
            reviewedAt=item.reviewed_at,
            metadata=item.metadata,
            createdAt=item.created_at,
        )
        for item in repository.list_events(
            model_name=model_name,
            event_type=event_type,
            status=status,
            operator=operator,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
        )
    ]


@router.get("/governance-alerts", response_model=list[GovernanceAlertResponse])
async def list_governance_alerts(
    model_name: str | None = Query(default=None, alias="modelName"),
    operator: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    alert_type: str | None = Query(default=None, alias="alertType"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db_session),
) -> list[GovernanceAlertResponse]:
    alerts = ModelGovernanceService(
        version_repository=MLModelVersionRepository(session),
        training_run_repository=MLTrainingRunRepository(session),
        governance_event_repository=MLGovernanceEventRepository(session),
    ).list_governance_alerts(
        model_name=model_name,
        operator=operator,
        severity=severity,
        alert_type=alert_type,
        limit=limit,
    )
    return [
        GovernanceAlertResponse(
            id=item.id,
            eventId=item.event_id,
            modelName=item.model_name,
            eventType=item.event_type,
            operator=item.operator,
            status=item.status,
            alertType=item.alert_type,
            severity=item.severity,
            message=item.message,
            fromVersion=item.from_version,
            toVersion=item.to_version,
            expiresAt=item.expires_at,
            createdAt=item.created_at,
            metadata=item.metadata,
        )
        for item in alerts
    ]


@router.post("/governance-alerts/notify", response_model=GovernanceAlertNotificationResponse)
async def notify_governance_alerts(
    request: GovernanceAlertNotificationRequest,
    session: Session = Depends(get_db_session),
) -> GovernanceAlertNotificationResponse:
    alerts = ModelGovernanceService(
        version_repository=MLModelVersionRepository(session),
        training_run_repository=MLTrainingRunRepository(session),
        governance_event_repository=MLGovernanceEventRepository(session),
    ).list_governance_alerts(
        model_name=request.model_name,
        operator=request.operator,
        severity=request.severity,
        alert_type=request.alert_type,
        limit=request.limit,
    )
    result = GovernanceAlertNotifier().notify(
        alerts=alerts,
        channel=request.channel,
        destination=request.destination,
    )
    return GovernanceAlertNotificationResponse(
        channel=result.channel,
        destination=result.destination,
        deliveryCount=result.delivery_count,
        notifiedAlertIds=result.notified_alert_ids,
        deliveries=[
            GovernanceAlertNotificationDeliveryResponse(
                id=item.id,
                alertId=item.alert_id,
                channel=item.channel,
                destination=item.destination,
                subject=item.subject,
                body=item.body,
                payload=item.payload,
            )
            for item in result.deliveries
        ],
    )


@router.post("/validate", response_model=ModelArtifactValidationResponse)
async def validate_model_artifact(
    request: ValidateModelRequest,
    session: Session = Depends(get_db_session),
) -> ModelArtifactValidationResponse:
    repository = MLModelVersionRepository(session)
    registry = ModelRegistryService(repository)
    registry.ensure_default_versions()
    validation = registry.validate_model_version(
        model_name=request.model_name,
        model_version=request.model_version,
    )
    return ModelArtifactValidationResponse(
        artifactUri=validation.artifact_uri,
        framework=validation.framework,
        scheme=validation.scheme,
        exists=validation.exists,
        loadable=validation.loadable,
        resolvedPath=validation.resolved_path,
        loadedConfig=validation.loaded_config,
        loadedMetrics=validation.loaded_metrics,
        loadedRuntime=validation.loaded_runtime,
    )


@router.post("/register", response_model=ModelVersionResponse)
async def register_model_version(
    request: RegisterModelRequest,
    session: Session = Depends(get_db_session),
) -> ModelVersionResponse:
    repository = MLModelVersionRepository(session)
    registry = ModelRegistryService(repository)
    model = registry.register_version(
        model_name=request.model_name,
        model_version=request.model_version,
        framework=request.framework,
        artifact_uri=request.artifact_uri,
        config=request.config,
        metrics=request.metrics,
        activate=request.activate,
    )
    return ModelVersionResponse(
        id=model.id,
        modelName=model.model_name,
        modelVersion=model.model_version,
        framework=model.framework,
        status=model.status,
        artifactUri=model.artifact_uri,
        config=model.config,
        metrics=model.metrics,
    )


@router.post("/activate", response_model=ModelVersionResponse)
async def activate_model_version(
    request: ActivateModelRequest,
    session: Session = Depends(get_db_session),
) -> ModelVersionResponse:
    repository = MLModelVersionRepository(session)
    registry = ModelRegistryService(repository)
    registry.ensure_default_versions()
    model = repository.activate_version(
        model_name=request.model_name,
        model_version=request.model_version,
    )
    return ModelVersionResponse(
        id=model.id,
        modelName=model.model_name,
        modelVersion=model.model_version,
        framework=model.framework,
        status=model.status,
        artifactUri=model.artifact_uri,
        config=model.config,
        metrics=model.metrics,
    )


@router.post("/rollback", response_model=RollbackModelResponse)
async def rollback_model_version(
    request: RollbackModelRequest,
    session: Session = Depends(get_db_session),
) -> RollbackModelResponse:
    version_repository = MLModelVersionRepository(session)
    ModelRegistryService(version_repository).ensure_default_versions()
    result = ModelGovernanceService(
        version_repository=version_repository,
        training_run_repository=MLTrainingRunRepository(session),
        governance_event_repository=MLGovernanceEventRepository(session),
    ).rollback_active_model(
        model_name=request.model_name,
        target_version=request.target_version,
        operator=request.operator,
        approval_ticket=request.approval_ticket,
    )
    return RollbackModelResponse(
        modelName=result.model_name,
        fromVersion=result.from_version,
        toVersion=result.to_version,
        reason=result.reason,
        status=result.status,
        riskLevel=result.risk_level,
        executed=result.executed,
        governanceEventId=result.governance_event_id,
    )


@router.post("/governance-events/expire-pending", response_model=ExpirePendingGovernanceEventsResponse)
async def expire_pending_governance_events(
    request: ExpirePendingGovernanceEventsRequest,
    session: Session = Depends(get_db_session),
) -> ExpirePendingGovernanceEventsResponse:
    result = ModelGovernanceService(
        version_repository=MLModelVersionRepository(session),
        training_run_repository=MLTrainingRunRepository(session),
        governance_event_repository=MLGovernanceEventRepository(session),
    ).expire_pending_governance_events(
        model_name=request.model_name,
        pending_operator=request.pending_operator,
        operator=request.operator,
        limit=request.limit,
    )
    return ExpirePendingGovernanceEventsResponse(
        expiredCount=result.expired_count,
        expiredEventIds=result.expired_event_ids,
    )


@router.post("/governance-events/{event_id}/review", response_model=ReviewGovernanceEventResponse)
async def review_governance_event(
    event_id: str,
    request: ReviewGovernanceEventRequest,
    session: Session = Depends(get_db_session),
) -> ReviewGovernanceEventResponse:
    result = ModelGovernanceService(
        version_repository=MLModelVersionRepository(session),
        training_run_repository=MLTrainingRunRepository(session),
        governance_event_repository=MLGovernanceEventRepository(session),
    ).review_governance_event(
        event_id=event_id,
        reviewer=request.reviewer,
        action=request.action,
        comment=request.comment,
        approval_ticket=request.approval_ticket,
    )
    return ReviewGovernanceEventResponse(
        eventId=result.event_id,
        eventType=result.event_type,
        modelName=result.model_name,
        status=result.status,
        reviewer=result.reviewer,
        reviewedAt=result.reviewed_at,
        reason=result.reason,
        fromVersion=result.from_version,
        toVersion=result.to_version,
        executed=result.executed,
    )
