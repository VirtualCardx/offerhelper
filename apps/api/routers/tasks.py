from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from apps.worker.celery_app import celery_app
from apps.worker.tasks.expire_pending_governance import expire_pending_governance_events
from apps.worker.tasks.notify_governance_alerts import notify_governance_alerts
from apps.worker.tasks.rollback_model import rollback_active_model
from apps.worker.tasks.scan_governance_alerts import scan_governance_alerts
from apps.worker.tasks.sync_market_data import sync_market_snapshot, sync_market_snapshot_batch
from apps.worker.tasks.train_acceptance_model import train_acceptance_model
from src.shared.config.settings import get_settings


router = APIRouter(prefix="/tasks", tags=["Tasks"])
settings = get_settings()


class MarketSyncTaskRequest(BaseModel):
    position_id: str = Field(alias="positionId")
    city: str
    p25: str = Field(alias="P25")
    p50: str = Field(alias="P50")
    p75: str = Field(alias="P75")
    source: str


class TaskDispatchResponse(BaseModel):
    task_id: str = Field(alias="taskId")
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str = Field(alias="taskId")
    status: str
    result: dict[str, object] | None = None


class MarketSyncBatchItemRequest(BaseModel):
    position_id: str = Field(alias="positionId")
    city: str
    p25: str = Field(alias="P25")
    p50: str = Field(alias="P50")
    p75: str = Field(alias="P75")
    source: str


class MarketSyncBatchTaskRequest(BaseModel):
    records: list[MarketSyncBatchItemRequest]


class TaskScheduleResponse(BaseModel):
    task: str
    cron: str
    description: str


class AcceptanceModelTrainTaskRequest(BaseModel):
    model_name: str = Field(default="baseline-offer-acceptance", alias="modelName")
    model_version: str | None = Field(default=None, alias="modelVersion")
    framework: str = "xgboost"
    source: str = "db"
    activation_mode: Literal["always", "if_better", "never"] = Field(default="if_better", alias="activationMode")
    operator: str = "system"


class RollbackModelTaskRequest(BaseModel):
    model_name: str = Field(alias="modelName")
    target_version: str | None = Field(default=None, alias="targetVersion")
    operator: str = "system"
    approval_ticket: str | None = Field(default=None, alias="approvalTicket")


class ExpirePendingGovernanceTaskRequest(BaseModel):
    model_name: str | None = Field(default=None, alias="modelName")
    pending_operator: str | None = Field(default=None, alias="pendingOperator")
    operator: str = "governance-bot"
    limit: int = Field(default=100, ge=1, le=500)


class GovernanceAlertScanTaskRequest(BaseModel):
    model_name: str | None = Field(default=None, alias="modelName")
    operator: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class GovernanceAlertNotifyTaskRequest(BaseModel):
    model_name: str | None = Field(default=None, alias="modelName")
    operator: str | None = None
    severity: str | None = None
    alert_type: str | None = Field(default=None, alias="alertType")
    channel: Literal["log", "webhook-payload"] = "log"
    destination: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


@router.post("/market-sync", response_model=TaskDispatchResponse)
async def dispatch_market_sync_task(request: MarketSyncTaskRequest) -> TaskDispatchResponse:
    async_result = sync_market_snapshot.delay(
        position_id=request.position_id,
        city=request.city,
        p25=request.p25,
        p50=request.p50,
        p75=request.p75,
        source=request.source,
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.post("/market-sync/batch", response_model=TaskDispatchResponse)
async def dispatch_market_sync_batch_task(request: MarketSyncBatchTaskRequest) -> TaskDispatchResponse:
    async_result = sync_market_snapshot_batch.delay(
        records=[
            {
                "position_id": item.position_id,
                "city": item.city,
                "p25": item.p25,
                "p50": item.p50,
                "p75": item.p75,
                "source": item.source,
            }
            for item in request.records
        ]
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.post("/models/train", response_model=TaskDispatchResponse)
async def dispatch_acceptance_model_train_task(request: AcceptanceModelTrainTaskRequest) -> TaskDispatchResponse:
    async_result = train_acceptance_model.delay(
        model_name=request.model_name,
        model_version=request.model_version,
        framework=request.framework,
        source=request.source,
        activation_mode=request.activation_mode,
        operator=request.operator,
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.post("/models/rollback", response_model=TaskDispatchResponse)
async def dispatch_model_rollback_task(request: RollbackModelTaskRequest) -> TaskDispatchResponse:
    async_result = rollback_active_model.delay(
        model_name=request.model_name,
        target_version=request.target_version,
        operator=request.operator,
        approval_ticket=request.approval_ticket,
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.post("/models/governance-expire-pending", response_model=TaskDispatchResponse)
async def dispatch_expire_pending_governance_task(
    request: ExpirePendingGovernanceTaskRequest,
) -> TaskDispatchResponse:
    async_result = expire_pending_governance_events.delay(
        model_name=request.model_name,
        pending_operator=request.pending_operator,
        operator=request.operator,
        limit=request.limit,
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.post("/models/governance-alert-scan", response_model=TaskDispatchResponse)
async def dispatch_governance_alert_scan_task(
    request: GovernanceAlertScanTaskRequest,
) -> TaskDispatchResponse:
    async_result = scan_governance_alerts.delay(
        model_name=request.model_name,
        operator=request.operator,
        limit=request.limit,
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.post("/models/governance-alerts/notify", response_model=TaskDispatchResponse)
async def dispatch_governance_alert_notify_task(
    request: GovernanceAlertNotifyTaskRequest,
) -> TaskDispatchResponse:
    async_result = notify_governance_alerts.delay(
        model_name=request.model_name,
        operator=request.operator,
        severity=request.severity,
        alert_type=request.alert_type,
        channel=request.channel,
        destination=request.destination,
        limit=request.limit,
    )
    return TaskDispatchResponse(taskId=async_result.id, status=async_result.status)


@router.get("/schedules", response_model=list[TaskScheduleResponse])
async def list_task_schedules() -> list[TaskScheduleResponse]:
    return [
        TaskScheduleResponse(
            task="market.sync_demo_batch",
            cron=f"*/{settings.market_sync_schedule_minutes} * * * *",
            description="Scheduled market sync placeholder batch for local and production scheduler wiring.",
        ),
        TaskScheduleResponse(
            task="models.expire_pending_governance",
            cron=f"*/{settings.governance_pending_review_sweep_minutes} * * * *",
            description="Scheduled governance sweep that expires stale pending rollback approvals.",
        ),
        TaskScheduleResponse(
            task="models.scan_governance_alerts",
            cron=f"*/{settings.governance_pending_review_sweep_minutes} * * * *",
            description="Scheduled governance alert scan that summarizes pending and expired review risks.",
        ),
        TaskScheduleResponse(
            task="models.notify_governance_alerts",
            cron=f"*/{settings.governance_pending_review_sweep_minutes} * * * *",
            description="Scheduled governance alert notification task that renders channel-specific deliveries.",
        )
    ]


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    result = celery_app.AsyncResult(task_id)
    payload = result.result if isinstance(result.result, dict) else None
    return TaskStatusResponse(taskId=task_id, status=result.status, result=payload)
