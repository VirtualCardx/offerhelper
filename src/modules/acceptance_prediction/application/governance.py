from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re

from src.modules.acceptance_prediction.infrastructure.repositories import (
    MLGovernanceEvent,
    MLGovernanceEventRepository,
    MLModelVersionRepository,
    MLTrainingRunRepository,
)
from src.shared.config.settings import get_settings
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class RollbackResult:
    model_name: str
    from_version: str
    to_version: str
    reason: str
    status: str
    risk_level: str
    executed: bool
    governance_event_id: str


@dataclass(frozen=True)
class GovernanceReviewResult:
    event_id: str
    event_type: str
    model_name: str
    status: str
    reviewer: str
    reviewed_at: datetime | None
    reason: str
    from_version: str | None
    to_version: str | None
    executed: bool


@dataclass(frozen=True)
class GovernanceExpirationResult:
    expired_count: int
    expired_event_ids: list[str]


@dataclass(frozen=True)
class GovernanceAlert:
    id: str
    event_id: str
    model_name: str
    event_type: str
    operator: str
    status: str
    alert_type: str
    severity: str
    message: str
    from_version: str | None
    to_version: str | None
    expires_at: datetime | None
    created_at: datetime
    metadata: dict[str, object]


@dataclass(frozen=True)
class GovernanceAlertScanResult:
    alert_count: int
    high_severity_count: int
    critical_severity_count: int
    alert_ids: list[str]


class ModelGovernanceService:
    def __init__(
        self,
        *,
        version_repository: MLModelVersionRepository,
        training_run_repository: MLTrainingRunRepository,
        governance_event_repository: MLGovernanceEventRepository,
    ) -> None:
        self.version_repository = version_repository
        self.training_run_repository = training_run_repository
        self.governance_event_repository = governance_event_repository
        self.settings = get_settings()

    def rollback_active_model(
        self,
        *,
        model_name: str,
        target_version: str | None = None,
        operator: str = "system",
        approval_ticket: str | None = None,
    ) -> RollbackResult:
        current_active = self.version_repository.get_active_version(model_name=model_name)
        resolved_target_version = target_version
        reason = "Rollback target explicitly requested."
        if resolved_target_version is None:
            activated_run = self.training_run_repository.get_latest_activated_run(
                model_name=model_name,
                model_version=current_active.model_version,
            )
            if activated_run is None or activated_run.previous_active_version is None:
                raise DomainValidationError(
                    f"No rollback snapshot is available for active model '{model_name}:{current_active.model_version}'."
                )
            resolved_target_version = activated_run.previous_active_version
            reason = "Rollback target resolved from latest activation snapshot."

        previous_snapshot_version = self._resolve_previous_snapshot_version(
            model_name=model_name,
            current_version=current_active.model_version,
        )
        self._validate_target_within_protection_window(
            model_name=model_name,
            current_version=current_active.model_version,
            target_version=resolved_target_version,
            previous_snapshot_version=previous_snapshot_version,
        )
        risk_level = self._assess_risk(
            target_version=resolved_target_version,
            previous_snapshot_version=previous_snapshot_version,
        )
        if (
            risk_level == "HIGH"
            and self.settings.high_risk_rollback_requires_approval
            and not approval_ticket
        ):
            requested_at = datetime.now(UTC)
            expires_at = requested_at + timedelta(hours=self.settings.governance_pending_review_ttl_hours)
            pending_event = self.governance_event_repository.create(
                model_name=model_name,
                event_type="ROLLBACK",
                operator=operator,
                approval_ticket=None,
                risk_level=risk_level,
                status="PENDING",
                reason="High-risk rollback requires approval before execution.",
                from_version=current_active.model_version,
                to_version=resolved_target_version,
                metadata={
                    "requiresApproval": True,
                    "currentVersion": current_active.model_version,
                    "targetVersion": resolved_target_version,
                    "requestedAt": requested_at.isoformat(),
                    "expiresAt": expires_at.isoformat(),
                },
            )
            return RollbackResult(
                model_name=model_name,
                from_version=current_active.model_version,
                to_version=resolved_target_version,
                reason=pending_event.reason,
                status="PENDING",
                risk_level=risk_level,
                executed=False,
                governance_event_id=pending_event.id,
            )

        activated = self.version_repository.activate_version(
            model_name=model_name,
            model_version=resolved_target_version,
        )
        event_status = "APPROVED" if approval_ticket else "SUCCESS"
        completed_event = self.governance_event_repository.create(
            model_name=model_name,
            event_type="ROLLBACK",
            operator=operator,
            approval_ticket=approval_ticket,
            risk_level=risk_level,
            status=event_status,
            reason=reason,
            from_version=current_active.model_version,
            to_version=activated.model_version,
            metadata={
                "requiresApproval": risk_level == "HIGH",
                "executed": True,
                "reviewedBy": operator if approval_ticket else None,
                "reviewedAt": datetime.now(UTC).isoformat() if approval_ticket else None,
            },
        )
        return RollbackResult(
            model_name=model_name,
            from_version=current_active.model_version,
            to_version=activated.model_version,
            reason=reason,
            status=activated.status,
            risk_level=risk_level,
            executed=True,
            governance_event_id=completed_event.id,
        )

    def review_governance_event(
        self,
        *,
        event_id: str,
        reviewer: str,
        action: str,
        comment: str | None = None,
        approval_ticket: str | None = None,
    ) -> GovernanceReviewResult:
        event = self.governance_event_repository.get_by_id(event_id=event_id)
        if event.status != "PENDING":
            raise DomainValidationError(f"Governance event '{event_id}' is not pending review.")
        if event.event_type != "ROLLBACK":
            raise DomainValidationError(f"Governance event '{event_id}' does not support review actions.")
        if action not in {"APPROVE", "REJECT"}:
            raise DomainValidationError("Review action must be APPROVE or REJECT.")
        if self._is_event_expired(event):
            self._expire_event(
                event_id=event_id,
                reviewer=reviewer,
                reason="Rollback request expired before review.",
                approval_ticket=approval_ticket,
            )
            raise DomainValidationError(f"Governance event '{event_id}' expired before review.")
        if action == "APPROVE" and not approval_ticket:
            raise DomainValidationError("Approval ticket is required when approving a pending rollback event.")

        if action == "REJECT":
            reviewed = self.governance_event_repository.update_review(
                event_id=event_id,
                status="REJECTED",
                reviewer=reviewer,
                reason=comment or "Rollback request was rejected.",
                approval_ticket=approval_ticket,
                metadata={
                    "approvalTicket": approval_ticket,
                    "executed": False,
                },
            )
            return GovernanceReviewResult(
                event_id=reviewed.id,
                event_type=reviewed.event_type,
                model_name=reviewed.model_name,
                status=reviewed.status,
                reviewer=reviewed.reviewed_by or reviewer,
                reviewed_at=reviewed.reviewed_at,
                reason=reviewed.reason,
                from_version=reviewed.from_version,
                to_version=reviewed.to_version,
                executed=False,
            )

        activated = self.version_repository.activate_version(
            model_name=event.model_name,
            model_version=event.to_version or "",
        )
        reviewed = self.governance_event_repository.update_review(
            event_id=event_id,
            status="APPROVED",
            reviewer=reviewer,
            reason=comment or "Rollback request was approved and executed.",
            approval_ticket=approval_ticket,
            metadata={
                "approvalTicket": approval_ticket,
                "executed": True,
                "activatedVersion": activated.model_version,
            },
        )
        return GovernanceReviewResult(
            event_id=reviewed.id,
            event_type=reviewed.event_type,
            model_name=reviewed.model_name,
            status=reviewed.status,
            reviewer=reviewed.reviewed_by or reviewer,
            reviewed_at=reviewed.reviewed_at,
            reason=reviewed.reason,
            from_version=reviewed.from_version,
            to_version=reviewed.to_version,
            executed=True,
        )

    def expire_pending_governance_events(
        self,
        *,
        model_name: str | None = None,
        pending_operator: str | None = None,
        operator: str = "system",
        limit: int = 100,
    ) -> GovernanceExpirationResult:
        expired_event_ids: list[str] = []
        pending_events = self.governance_event_repository.list_events(
            model_name=model_name,
            event_type="ROLLBACK",
            status="PENDING",
            operator=pending_operator,
            limit=limit,
        )
        for event in pending_events:
            if not self._is_event_expired(event):
                continue
            expired = self._expire_event(
                event_id=event.id,
                reviewer=operator,
                reason="Pending governance review expired before approval.",
            )
            expired_event_ids.append(expired.id)
        return GovernanceExpirationResult(
            expired_count=len(expired_event_ids),
            expired_event_ids=expired_event_ids,
        )

    def list_governance_alerts(
        self,
        *,
        model_name: str | None = None,
        operator: str | None = None,
        severity: str | None = None,
        alert_type: str | None = None,
        limit: int = 50,
    ) -> list[GovernanceAlert]:
        events = self.governance_event_repository.list_events(
            model_name=model_name,
            event_type="ROLLBACK",
            operator=operator,
            limit=max(limit * 5, 100),
        )
        alerts = [
            alert
            for event in events
            for alert in [self._build_alert(event)]
            if alert is not None
        ]
        if severity is not None:
            alerts = [item for item in alerts if item.severity == severity]
        if alert_type is not None:
            alerts = [item for item in alerts if item.alert_type == alert_type]
        return alerts[:limit]

    def scan_governance_alerts(
        self,
        *,
        model_name: str | None = None,
        operator: str | None = None,
        limit: int = 50,
    ) -> GovernanceAlertScanResult:
        alerts = self.list_governance_alerts(
            model_name=model_name,
            operator=operator,
            limit=limit,
        )
        return GovernanceAlertScanResult(
            alert_count=len(alerts),
            high_severity_count=sum(1 for item in alerts if item.severity == "HIGH"),
            critical_severity_count=sum(1 for item in alerts if item.severity == "CRITICAL"),
            alert_ids=[item.id for item in alerts],
        )

    def _assess_risk(
        self,
        *,
        target_version: str,
        previous_snapshot_version: str | None,
    ) -> str:
        if previous_snapshot_version is not None and target_version == previous_snapshot_version:
            return "LOW"
        return "HIGH"

    def _validate_target_within_protection_window(
        self,
        *,
        model_name: str,
        current_version: str,
        target_version: str,
        previous_snapshot_version: str | None,
    ) -> None:
        if target_version == current_version:
            return
        protected_versions = self._protected_versions(model_name=model_name)
        if target_version == previous_snapshot_version:
            return
        if target_version not in protected_versions:
            raise DomainValidationError(
                f"Rollback target '{model_name}:{target_version}' is outside the protected rollback window."
            )

    def _resolve_previous_snapshot_version(
        self,
        *,
        model_name: str,
        current_version: str,
    ) -> str | None:
        activated_run = self.training_run_repository.get_latest_activated_run(
            model_name=model_name,
            model_version=current_version,
        )
        if activated_run is None:
            return None
        return activated_run.previous_active_version

    def _protected_versions(self, *, model_name: str) -> list[str]:
        versions = [
            item.model_version
            for item in self.version_repository.list_versions(model_name=model_name)
            if self._parse_semantic_version(item.model_version) is not None
        ]
        versions = sorted(versions, key=lambda item: self._parse_semantic_version(item) or (0, 0, 0), reverse=True)
        return versions[: self.settings.model_rollback_max_candidate_versions]

    @staticmethod
    def _parse_semantic_version(model_version: str) -> tuple[int, int, int] | None:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", model_version)
        if match is None:
            return None
        return tuple(int(part) for part in match.groups())

    def _expire_event(
        self,
        *,
        event_id: str,
        reviewer: str,
        reason: str,
        approval_ticket: str | None = None,
    ) -> MLGovernanceEvent:
        return self.governance_event_repository.update_review(
            event_id=event_id,
            status="EXPIRED",
            reviewer=reviewer,
            reason=reason,
            approval_ticket=approval_ticket,
            metadata={
                "approvalTicket": approval_ticket,
                "executed": False,
                "expired": True,
                "expiredAt": datetime.now(UTC).isoformat(),
            },
        )

    @staticmethod
    def _is_event_expired(event: MLGovernanceEvent) -> bool:
        expires_at = ModelGovernanceService._parse_datetime(event.metadata.get("expiresAt"))
        if expires_at is None:
            return False
        return expires_at <= datetime.now(UTC)

    def _build_alert(self, event: MLGovernanceEvent) -> GovernanceAlert | None:
        expires_at = self._parse_datetime(event.metadata.get("expiresAt"))
        now = datetime.now(UTC)
        alert_type: str | None = None
        severity: str | None = None
        message: str | None = None

        if event.status == "PENDING":
            if expires_at is not None and expires_at <= now:
                alert_type = "OVERDUE_PENDING_REVIEW"
                severity = "CRITICAL"
                message = "Pending high-risk rollback review is overdue and requires immediate attention."
            elif expires_at is not None and expires_at <= now + timedelta(
                minutes=self.settings.governance_pending_review_alert_window_minutes
            ):
                alert_type = "EXPIRING_PENDING_REVIEW"
                severity = "HIGH"
                message = "Pending high-risk rollback review is approaching its expiration window."
            else:
                alert_type = "PENDING_REVIEW"
                severity = "MEDIUM"
                message = "High-risk rollback is pending governance review."
        elif event.status == "EXPIRED":
            alert_type = "EXPIRED_REVIEW"
            severity = "HIGH"
            message = "Pending high-risk rollback expired before review completion."

        if alert_type is None or severity is None or message is None:
            return None

        return GovernanceAlert(
            id=f"{event.id}:{alert_type}",
            event_id=event.id,
            model_name=event.model_name,
            event_type=event.event_type,
            operator=event.operator,
            status=event.status,
            alert_type=alert_type,
            severity=severity,
            message=message,
            from_version=event.from_version,
            to_version=event.to_version,
            expires_at=expires_at,
            created_at=event.created_at,
            metadata=event.metadata,
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
