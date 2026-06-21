from __future__ import annotations

from dataclasses import dataclass

from src.modules.acceptance_prediction.application.governance import GovernanceAlert
from src.shared.config.settings import get_settings
from src.shared.presentation.errors import DomainValidationError


@dataclass(frozen=True)
class GovernanceNotificationDelivery:
    id: str
    alert_id: str
    channel: str
    destination: str
    subject: str
    body: str
    payload: dict[str, object]


@dataclass(frozen=True)
class GovernanceNotificationResult:
    channel: str
    destination: str
    delivery_count: int
    notified_alert_ids: list[str]
    deliveries: list[GovernanceNotificationDelivery]


class GovernanceNotificationChannel:
    channel_name: str

    def send(
        self,
        *,
        alerts: list[GovernanceAlert],
        destination: str | None = None,
    ) -> GovernanceNotificationResult:
        resolved_destination = self.resolve_destination(destination=destination)
        deliveries = [
            self.build_delivery(alert=alert, destination=resolved_destination)
            for alert in alerts
        ]
        return GovernanceNotificationResult(
            channel=self.channel_name,
            destination=resolved_destination,
            delivery_count=len(deliveries),
            notified_alert_ids=[item.alert_id for item in deliveries],
            deliveries=deliveries,
        )

    def resolve_destination(self, *, destination: str | None = None) -> str:
        raise NotImplementedError

    def build_delivery(
        self,
        *,
        alert: GovernanceAlert,
        destination: str,
    ) -> GovernanceNotificationDelivery:
        raise NotImplementedError

    @staticmethod
    def _subject(alert: GovernanceAlert) -> str:
        return f"[{alert.severity}] Governance alert for {alert.model_name}"

    @staticmethod
    def _body(alert: GovernanceAlert) -> str:
        route = f"{alert.from_version or 'unknown'} -> {alert.to_version or 'unknown'}"
        return (
            f"{alert.message} "
            f"(alertType={alert.alert_type}, operator={alert.operator}, rollback={route}, status={alert.status})"
        )

    @staticmethod
    def _payload(alert: GovernanceAlert) -> dict[str, object]:
        return {
            "alertId": alert.id,
            "eventId": alert.event_id,
            "modelName": alert.model_name,
            "eventType": alert.event_type,
            "operator": alert.operator,
            "status": alert.status,
            "alertType": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "fromVersion": alert.from_version,
            "toVersion": alert.to_version,
            "expiresAt": None if alert.expires_at is None else alert.expires_at.isoformat(),
            "createdAt": alert.created_at.isoformat(),
            "metadata": alert.metadata,
        }


class LogGovernanceNotificationChannel(GovernanceNotificationChannel):
    channel_name = "log"

    def resolve_destination(self, *, destination: str | None = None) -> str:
        return destination or "stdout"

    def build_delivery(
        self,
        *,
        alert: GovernanceAlert,
        destination: str,
    ) -> GovernanceNotificationDelivery:
        payload = self._payload(alert)
        return GovernanceNotificationDelivery(
            id=f"{alert.id}:{self.channel_name}",
            alert_id=alert.id,
            channel=self.channel_name,
            destination=destination,
            subject=self._subject(alert),
            body=self._body(alert),
            payload=payload,
        )


class WebhookPayloadGovernanceNotificationChannel(GovernanceNotificationChannel):
    channel_name = "webhook-payload"

    def resolve_destination(self, *, destination: str | None = None) -> str:
        return destination or "https://example.invalid/governance-alerts"

    def build_delivery(
        self,
        *,
        alert: GovernanceAlert,
        destination: str,
    ) -> GovernanceNotificationDelivery:
        payload = {
            "destination": destination,
            "notification": self._payload(alert),
        }
        return GovernanceNotificationDelivery(
            id=f"{alert.id}:{self.channel_name}",
            alert_id=alert.id,
            channel=self.channel_name,
            destination=destination,
            subject=self._subject(alert),
            body=self._body(alert),
            payload=payload,
        )


class GovernanceAlertNotifier:
    def __init__(self) -> None:
        settings = get_settings()
        self.default_channel = settings.governance_notification_default_channel
        self.channels: dict[str, GovernanceNotificationChannel] = {
            "log": LogGovernanceNotificationChannel(),
            "webhook-payload": WebhookPayloadGovernanceNotificationChannel(),
        }

    def notify(
        self,
        *,
        alerts: list[GovernanceAlert],
        channel: str | None = None,
        destination: str | None = None,
    ) -> GovernanceNotificationResult:
        resolved_channel = channel or self.default_channel
        adapter = self.channels.get(resolved_channel)
        if adapter is None:
            raise DomainValidationError(
                f"Unsupported governance notification channel '{resolved_channel}'."
            )
        return adapter.send(alerts=alerts, destination=destination)
