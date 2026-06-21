from __future__ import annotations

import pickle
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from src.modules.acceptance_prediction.infrastructure.repositories import MLModelVersionRepository
from src.modules.acceptance_prediction.domain.services import WeightedProbabilityModel
from src.shared.config.settings import get_settings
from src.shared.infrastructure.db.session import SessionLocal, init_db


def test_list_and_activate_model_versions(client: TestClient) -> None:
    artifact_dir = Path(__file__).resolve().parents[2] / "artifacts" / "acceptance_prediction"
    artifact_uri = (artifact_dir / "baseline-offer-acceptance-0.3.0.json").as_uri()
    model_path = artifact_dir / "baseline-offer-acceptance-0.3.0.pkl"

    with model_path.open("wb") as artifact_file:
        pickle.dump(
            WeightedProbabilityModel(
                intercept=-0.61,
                coefficients=[1.0, 0.8, 0.01, -0.25],
            ),
            artifact_file,
        )

    versions_response = client.get("/api/v1/models/versions", params={"modelName": "baseline-offer-acceptance"})
    assert versions_response.status_code == 200
    versions_payload = versions_response.json()
    assert len(versions_payload) >= 2
    assert versions_payload[0]["artifactUri"].startswith("registry://")
    assert "base_probability" in versions_payload[0]["config"]

    register_response = client.post(
        "/api/v1/models/register",
        json={
            "modelName": "baseline-offer-acceptance",
            "modelVersion": "0.3.0",
            "framework": "sklearn",
            "artifactUri": artifact_uri,
            "config": {
                "base_probability": "0.10",
                "offer_market_bonus": "0.01",
            },
            "metrics": {"auc": 0.84},
            "activate": False,
        },
    )
    assert register_response.status_code == 200
    register_payload = register_response.json()
    assert register_payload["modelVersion"] == "0.3.0"
    assert register_payload["framework"] == "sklearn"
    assert register_payload["status"] == "INACTIVE"

    validate_response = client.post(
        "/api/v1/models/validate",
        json={
            "modelName": "baseline-offer-acceptance",
            "modelVersion": "0.3.0",
        },
    )
    assert validate_response.status_code == 200
    validate_payload = validate_response.json()
    assert validate_payload["artifactUri"] == artifact_uri
    assert validate_payload["scheme"] == "file"
    assert validate_payload["loadable"] is True
    assert validate_payload["loadedConfig"]["base_probability"] == "0.50"
    assert validate_payload["resolvedPath"].endswith("baseline-offer-acceptance-0.3.0.json")
    assert validate_payload["loadedRuntime"]["type"] == "python-pickle-proba"
    assert validate_payload["loadedRuntime"]["resolvedModelPath"].endswith("baseline-offer-acceptance-0.3.0.pkl")

    activate_response = client.post(
        "/api/v1/models/activate",
        json={
            "modelName": "baseline-offer-acceptance",
            "modelVersion": "0.2.0",
        },
    )
    assert activate_response.status_code == 200
    activate_payload = activate_response.json()
    assert activate_payload["modelVersion"] == "0.2.0"
    assert activate_payload["status"] == "ACTIVE"

    active_response = client.get("/api/v1/models/active", params={"modelName": "baseline-offer-acceptance"})
    assert active_response.status_code == 200
    active_payload = active_response.json()
    assert active_payload["modelVersion"] == "0.2.0"
    assert active_payload["artifactUri"] == "registry://baseline-offer-acceptance/0.2.0"


def test_dispatch_market_sync_task(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    task_response = client.post(
        "/api/v1/tasks/market-sync",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Beijing",
            "P25": "28000",
            "P50": "38000",
            "P75": "48000",
            "source": "scheduled-sync",
        },
    )
    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["status"] in {"SUCCESS", "PENDING"}

    status_response = client.get(f"/api/v1/tasks/{payload['taskId']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] in {"SUCCESS", "PENDING"}


def test_dispatch_market_sync_batch_and_list_schedules(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    batch_response = client.post(
        "/api/v1/tasks/market-sync/batch",
        json={
            "records": [
                {
                    "positionId": reference_ids["position_id"],
                    "city": "Shanghai",
                    "P25": "25000",
                    "P50": "35000",
                    "P75": "45000",
                    "source": "batch-sync",
                },
                {
                    "positionId": reference_ids["position_id"],
                    "city": "Guangzhou",
                    "P25": "24000",
                    "P50": "34000",
                    "P75": "44000",
                    "source": "batch-sync",
                },
            ]
        },
    )
    assert batch_response.status_code == 200
    batch_payload = batch_response.json()
    assert batch_payload["status"] in {"SUCCESS", "PENDING"}

    status_response = client.get(f"/api/v1/tasks/{batch_payload['taskId']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] in {"SUCCESS", "PENDING"}

    schedules_response = client.get("/api/v1/tasks/schedules")
    assert schedules_response.status_code == 200
    schedules_payload = schedules_response.json()
    assert len(schedules_payload) == 4
    assert {item["task"] for item in schedules_payload} == {
        "market.sync_demo_batch",
        "models.expire_pending_governance",
        "models.scan_governance_alerts",
        "models.notify_governance_alerts",
    }


def test_dispatch_acceptance_model_train_task(client: TestClient) -> None:
    task_response = client.post(
        "/api/v1/tasks/models/train",
        json={
            "modelName": "baseline-offer-acceptance",
            "modelVersion": "0.7.1",
            "framework": "xgboost",
            "source": "demo",
            "activationMode": "always",
            "operator": "ml-ops",
        },
    )
    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["status"] in {"SUCCESS", "PENDING"}

    status_response = client.get(f"/api/v1/tasks/{payload['taskId']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] in {"SUCCESS", "PENDING"}
    assert status_payload["result"]["modelVersion"] == "0.7.1"
    assert status_payload["result"]["registeredStatus"] == "ACTIVE"
    assert status_payload["result"]["trainingRunId"]
    assert status_payload["result"]["governanceEventId"]
    assert status_payload["result"]["source"] == "demo"
    assert status_payload["result"]["operator"] == "ml-ops"
    assert status_payload["result"]["activationMode"] == "always"
    assert status_payload["result"]["activated"] is True
    assert status_payload["result"]["artifactUri"].endswith("baseline-offer-acceptance-0.7.1.json")
    assert status_payload["result"]["activationReason"] == "Activation mode is set to always."


def test_list_training_runs_and_rollback_model(client: TestClient) -> None:
    train_response = client.post(
        "/api/v1/tasks/models/train",
        json={
            "modelName": "baseline-offer-acceptance",
            "modelVersion": "0.7.2",
            "framework": "xgboost",
            "source": "demo",
            "activationMode": "always",
        },
    )
    assert train_response.status_code == 200
    train_task_id = train_response.json()["taskId"]

    status_response = client.get(f"/api/v1/tasks/{train_task_id}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["result"]["modelVersion"] == "0.7.2"

    runs_response = client.get("/api/v1/models/training-runs", params={"modelName": "baseline-offer-acceptance"})
    assert runs_response.status_code == 200
    runs_payload = runs_response.json()
    assert isinstance(runs_payload, list)

    governance_response = client.get(
        "/api/v1/models/governance-events",
        params={"modelName": "baseline-offer-acceptance", "eventType": "TRAIN"},
    )
    assert governance_response.status_code == 200
    governance_payload = governance_response.json()
    assert isinstance(governance_payload, list)

    rollback_response = client.post(
        "/api/v1/models/rollback",
        json={
            "modelName": "baseline-offer-acceptance",
            "targetVersion": "0.2.0",
            "operator": "hr-admin",
            "approvalTicket": "APR-1001",
        },
    )
    assert rollback_response.status_code == 200
    rollback_payload = rollback_response.json()
    assert rollback_payload["modelName"] == "baseline-offer-acceptance"
    assert rollback_payload["toVersion"] == "0.2.0"
    assert rollback_payload["status"] == "ACTIVE"
    assert rollback_payload["riskLevel"] in {"LOW", "HIGH"}
    assert rollback_payload["executed"] is True
    assert rollback_payload["governanceEventId"]


def test_high_risk_rollback_creates_pending_event_and_can_be_reviewed(client: TestClient) -> None:
    rollback_response = client.post(
        "/api/v1/models/rollback",
        json={
            "modelName": "baseline-offer-acceptance",
            "targetVersion": "0.2.0",
            "operator": "risk-officer",
        },
    )
    assert rollback_response.status_code == 200
    rollback_payload = rollback_response.json()
    assert rollback_payload["status"] == "PENDING"
    assert rollback_payload["riskLevel"] == "HIGH"
    assert rollback_payload["executed"] is False

    events_response = client.get(
        "/api/v1/models/governance-events",
        params={
            "modelName": "baseline-offer-acceptance",
            "status": "PENDING",
            "operator": "risk-officer",
        },
    )
    assert events_response.status_code == 200
    events_payload = events_response.json()
    assert isinstance(events_payload, list)

    review_response = client.post(
        f"/api/v1/models/governance-events/{rollback_payload['governanceEventId']}/review",
        json={
            "action": "APPROVE",
            "reviewer": "director",
            "comment": "Approved after governance review.",
            "approvalTicket": "APR-2001",
        },
    )
    assert review_response.status_code == 200
    review_payload = review_response.json()
    assert review_payload["status"] == "APPROVED"
    assert review_payload["executed"] is True
    assert review_payload["reviewer"] == "director"


def test_pending_high_risk_rollback_review_requires_approval_ticket(client: TestClient) -> None:
    rollback_response = client.post(
        "/api/v1/models/rollback",
        json={
            "modelName": "baseline-offer-acceptance",
            "targetVersion": "0.2.0",
            "operator": "risk-officer",
        },
    )
    assert rollback_response.status_code == 200
    rollback_payload = rollback_response.json()
    assert rollback_payload["status"] == "PENDING"

    review_response = client.post(
        f"/api/v1/models/governance-events/{rollback_payload['governanceEventId']}/review",
        json={
            "action": "APPROVE",
            "reviewer": "director",
            "comment": "Missing approval ticket.",
        },
    )
    assert review_response.status_code == 400
    review_payload = review_response.json()
    assert review_payload["code"] == "DOMAIN_VALIDATION_ERROR"
    assert review_payload["message"] == "Approval ticket is required when approving a pending rollback event."


def test_expire_pending_governance_events_api(client: TestClient) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    settings.governance_pending_review_ttl_hours = 0

    try:
        rollback_response = client.post(
            "/api/v1/models/rollback",
            json={
                "modelName": "baseline-offer-acceptance",
                "targetVersion": "0.2.0",
                "operator": "risk-officer",
            },
        )
        assert rollback_response.status_code == 200
        rollback_payload = rollback_response.json()
        assert rollback_payload["status"] == "PENDING"

        expire_response = client.post(
            "/api/v1/models/governance-events/expire-pending",
            json={
                "modelName": "baseline-offer-acceptance",
                "operator": "governance-bot",
                "limit": 50,
            },
        )
        assert expire_response.status_code == 200
        expire_payload = expire_response.json()
        assert expire_payload["expiredCount"] == 1
        assert expire_payload["expiredEventIds"] == [rollback_payload["governanceEventId"]]

        events_response = client.get(
            "/api/v1/models/governance-events",
            params={
                "modelName": "baseline-offer-acceptance",
                "status": "EXPIRED",
            },
        )
        assert events_response.status_code == 200
        events_payload = events_response.json()
        assert len(events_payload) == 1
        assert events_payload[0]["status"] == "EXPIRED"
        assert events_payload[0]["metadata"]["expired"] is True

        review_response = client.post(
            f"/api/v1/models/governance-events/{rollback_payload['governanceEventId']}/review",
            json={
                "action": "APPROVE",
                "reviewer": "director",
                "comment": "Late approval attempt.",
                "approvalTicket": "APR-LATE",
            },
        )
        assert review_response.status_code == 400
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours


def test_list_governance_alerts_for_pending_and_expired_reviews(client: TestClient) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    original_alert_window_minutes = settings.governance_pending_review_alert_window_minutes
    settings.governance_pending_review_ttl_hours = 1
    settings.governance_pending_review_alert_window_minutes = 24 * 60

    try:
        rollback_response = client.post(
            "/api/v1/models/rollback",
            json={
                "modelName": "baseline-offer-acceptance",
                "targetVersion": "0.2.0",
                "operator": "risk-officer",
            },
        )
        assert rollback_response.status_code == 200
        rollback_payload = rollback_response.json()

        alerts_response = client.get(
            "/api/v1/models/governance-alerts",
            params={
                "modelName": "baseline-offer-acceptance",
                "operator": "risk-officer",
            },
        )
        assert alerts_response.status_code == 200
        alerts_payload = alerts_response.json()
        assert len(alerts_payload) == 1
        assert alerts_payload[0]["eventId"] == rollback_payload["governanceEventId"]
        assert alerts_payload[0]["alertType"] == "EXPIRING_PENDING_REVIEW"
        assert alerts_payload[0]["severity"] == "HIGH"
        assert alerts_payload[0]["expiresAt"] is not None

        settings.governance_pending_review_ttl_hours = 0
        expired_rollback_response = client.post(
            "/api/v1/models/rollback",
            json={
                "modelName": "baseline-offer-acceptance",
                "targetVersion": "0.2.0",
                "operator": "risk-officer",
            },
        )
        assert expired_rollback_response.status_code == 200
        expired_rollback_payload = expired_rollback_response.json()

        expire_response = client.post(
            "/api/v1/models/governance-events/expire-pending",
            json={
                "modelName": "baseline-offer-acceptance",
                "pendingOperator": "risk-officer",
                "operator": "governance-bot",
                "limit": 50,
            },
        )
        assert expire_response.status_code == 200

        expired_alerts_response = client.get(
            "/api/v1/models/governance-alerts",
            params={
                "modelName": "baseline-offer-acceptance",
                "operator": "risk-officer",
                "alertType": "EXPIRED_REVIEW",
            },
        )
        assert expired_alerts_response.status_code == 200
        expired_alerts_payload = expired_alerts_response.json()
        assert len(expired_alerts_payload) == 1
        assert expired_alerts_payload[0]["eventId"] == expired_rollback_payload["governanceEventId"]
        assert expired_alerts_payload[0]["status"] == "EXPIRED"
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours
        settings.governance_pending_review_alert_window_minutes = original_alert_window_minutes


def test_notify_governance_alerts_api_returns_log_deliveries(client: TestClient) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    original_alert_window_minutes = settings.governance_pending_review_alert_window_minutes
    settings.governance_pending_review_ttl_hours = 1
    settings.governance_pending_review_alert_window_minutes = 24 * 60

    try:
        rollback_response = client.post(
            "/api/v1/models/rollback",
            json={
                "modelName": "baseline-offer-acceptance",
                "targetVersion": "0.2.0",
                "operator": "risk-officer",
            },
        )
        assert rollback_response.status_code == 200

        notify_response = client.post(
            "/api/v1/models/governance-alerts/notify",
            json={
                "modelName": "baseline-offer-acceptance",
                "operator": "risk-officer",
                "channel": "log",
                "limit": 50,
            },
        )
        assert notify_response.status_code == 200
        notify_payload = notify_response.json()
        assert notify_payload["channel"] == "log"
        assert notify_payload["destination"] == "stdout"
        assert notify_payload["deliveryCount"] == 1
        assert len(notify_payload["deliveries"]) == 1
        assert notify_payload["deliveries"][0]["channel"] == "log"
        assert "Governance alert" in notify_payload["deliveries"][0]["subject"]
        assert "approaching its expiration window" in notify_payload["deliveries"][0]["body"]
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours
        settings.governance_pending_review_alert_window_minutes = original_alert_window_minutes


def test_dispatch_model_rollback_task(client: TestClient) -> None:
    task_response = client.post(
        "/api/v1/tasks/models/rollback",
        json={
            "modelName": "baseline-offer-acceptance",
            "operator": "risk-officer",
            "approvalTicket": "APR-9001",
        },
    )
    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["status"] in {"SUCCESS", "PENDING"}

    status_response = client.get(f"/api/v1/tasks/{payload['taskId']}")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] in {"SUCCESS", "PENDING"}
    assert status_payload["result"]["modelName"] == "baseline-offer-acceptance"
    assert status_payload["result"]["toVersion"]
    assert status_payload["result"]["registeredStatus"] == "ACTIVE"
    assert status_payload["result"]["executed"] is True
    assert status_payload["result"]["governanceEventId"]
    assert status_payload["result"]["operator"] == "risk-officer"
    assert status_payload["result"]["approvalTicket"] == "APR-9001"


def test_dispatch_expire_pending_governance_task(client: TestClient) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    settings.governance_pending_review_ttl_hours = 0
    model_name = f"governance-expire-{uuid.uuid4()}"
    pending_operator = f"risk-officer-{uuid.uuid4()}"

    try:
        init_db()
        session = SessionLocal()
        try:
            repository = MLModelVersionRepository(session)
            repository.ensure_exists(
                model_name=model_name,
                model_version="0.9.0",
                framework="xgboost",
                status="ACTIVE",
                artifact_uri="file:///tmp/0.9.0.json",
                config={},
                metrics={"trainingAccuracy": 0.9, "trainingLogLoss": 0.1},
            )
            repository.ensure_exists(
                model_name=model_name,
                model_version="0.1.0",
                framework="rule-based",
                status="INACTIVE",
                artifact_uri=f"registry://{model_name}/0.1.0",
                config={},
                metrics={},
            )
        finally:
            session.close()

        rollback_task_response = client.post(
            "/api/v1/tasks/models/rollback",
            json={
                "modelName": model_name,
                "targetVersion": "0.1.0",
                "operator": pending_operator,
            },
        )
        assert rollback_task_response.status_code == 200
        rollback_task_payload = rollback_task_response.json()

        rollback_status_response = client.get(f"/api/v1/tasks/{rollback_task_payload['taskId']}")
        assert rollback_status_response.status_code == 200
        rollback_status_payload = rollback_status_response.json()
        assert rollback_status_payload["result"]["registeredStatus"] == "PENDING"
        assert rollback_status_payload["result"]["executed"] is False

        task_response = client.post(
            "/api/v1/tasks/models/governance-expire-pending",
            json={
                "modelName": model_name,
                "pendingOperator": pending_operator,
                "operator": "governance-bot",
                "limit": 50,
            },
        )
        assert task_response.status_code == 200
        payload = task_response.json()
        assert payload["status"] in {"SUCCESS", "PENDING"}

        status_response = client.get(f"/api/v1/tasks/{payload['taskId']}")
        assert status_response.status_code == 200
        status_payload = status_response.json()
        assert status_payload["status"] in {"SUCCESS", "PENDING"}
        assert status_payload["result"]["operator"] == "governance-bot"
        assert status_payload["result"]["pendingOperator"] == pending_operator
        assert status_payload["result"]["expiredCount"] == 1
        assert len(status_payload["result"]["expiredEventIds"]) == 1
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours


def test_dispatch_governance_alert_scan_task(client: TestClient) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    original_alert_window_minutes = settings.governance_pending_review_alert_window_minutes
    settings.governance_pending_review_ttl_hours = 1
    settings.governance_pending_review_alert_window_minutes = 24 * 60
    model_name = f"governance-alert-{uuid.uuid4()}"
    pending_operator = f"risk-officer-{uuid.uuid4()}"

    try:
        init_db()
        session = SessionLocal()
        try:
            repository = MLModelVersionRepository(session)
            repository.ensure_exists(
                model_name=model_name,
                model_version="0.9.0",
                framework="xgboost",
                status="ACTIVE",
                artifact_uri="file:///tmp/0.9.0.json",
                config={},
                metrics={"trainingAccuracy": 0.9, "trainingLogLoss": 0.1},
            )
            repository.ensure_exists(
                model_name=model_name,
                model_version="0.1.0",
                framework="rule-based",
                status="INACTIVE",
                artifact_uri=f"registry://{model_name}/0.1.0",
                config={},
                metrics={},
            )
        finally:
            session.close()

        rollback_task_response = client.post(
            "/api/v1/tasks/models/rollback",
            json={
                "modelName": model_name,
                "targetVersion": "0.1.0",
                "operator": pending_operator,
            },
        )
        assert rollback_task_response.status_code == 200

        task_response = client.post(
            "/api/v1/tasks/models/governance-alert-scan",
            json={
                "modelName": model_name,
                "operator": pending_operator,
                "limit": 50,
            },
        )
        assert task_response.status_code == 200
        payload = task_response.json()
        assert payload["status"] in {"SUCCESS", "PENDING"}

        status_response = client.get(f"/api/v1/tasks/{payload['taskId']}")
        assert status_response.status_code == 200
        status_payload = status_response.json()
        assert status_payload["status"] in {"SUCCESS", "PENDING"}
        assert status_payload["result"]["modelName"] == model_name
        assert status_payload["result"]["operator"] == pending_operator
        assert status_payload["result"]["alertCount"] == 1
        assert status_payload["result"]["highSeverityCount"] == 1
        assert status_payload["result"]["criticalSeverityCount"] == 0
        assert len(status_payload["result"]["alertIds"]) == 1
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours
        settings.governance_pending_review_alert_window_minutes = original_alert_window_minutes


def test_dispatch_governance_alert_notify_task(client: TestClient) -> None:
    settings = get_settings()
    original_ttl_hours = settings.governance_pending_review_ttl_hours
    original_alert_window_minutes = settings.governance_pending_review_alert_window_minutes
    settings.governance_pending_review_ttl_hours = 1
    settings.governance_pending_review_alert_window_minutes = 24 * 60
    model_name = f"governance-notify-{uuid.uuid4()}"
    pending_operator = f"risk-officer-{uuid.uuid4()}"

    try:
        init_db()
        session = SessionLocal()
        try:
            repository = MLModelVersionRepository(session)
            repository.ensure_exists(
                model_name=model_name,
                model_version="0.9.0",
                framework="xgboost",
                status="ACTIVE",
                artifact_uri="file:///tmp/0.9.0.json",
                config={},
                metrics={"trainingAccuracy": 0.9, "trainingLogLoss": 0.1},
            )
            repository.ensure_exists(
                model_name=model_name,
                model_version="0.1.0",
                framework="rule-based",
                status="INACTIVE",
                artifact_uri=f"registry://{model_name}/0.1.0",
                config={},
                metrics={},
            )
        finally:
            session.close()

        rollback_task_response = client.post(
            "/api/v1/tasks/models/rollback",
            json={
                "modelName": model_name,
                "targetVersion": "0.1.0",
                "operator": pending_operator,
            },
        )
        assert rollback_task_response.status_code == 200

        task_response = client.post(
            "/api/v1/tasks/models/governance-alerts/notify",
            json={
                "modelName": model_name,
                "operator": pending_operator,
                "channel": "webhook-payload",
                "destination": "https://notify.example.local/governance",
                "limit": 50,
            },
        )
        assert task_response.status_code == 200
        payload = task_response.json()
        assert payload["status"] in {"SUCCESS", "PENDING"}

        status_response = client.get(f"/api/v1/tasks/{payload['taskId']}")
        assert status_response.status_code == 200
        status_payload = status_response.json()
        assert status_payload["status"] in {"SUCCESS", "PENDING"}
        assert status_payload["result"]["modelName"] == model_name
        assert status_payload["result"]["operator"] == pending_operator
        assert status_payload["result"]["channel"] == "webhook-payload"
        assert status_payload["result"]["destination"] == "https://notify.example.local/governance"
        assert status_payload["result"]["deliveryCount"] == 1
        assert len(status_payload["result"]["deliveries"]) == 1
        assert status_payload["result"]["deliveries"][0]["channel"] == "webhook-payload"
        assert (
            status_payload["result"]["deliveries"][0]["payload"]["destination"]
            == "https://notify.example.local/governance"
        )
    finally:
        settings.governance_pending_review_ttl_hours = original_ttl_hours
        settings.governance_pending_review_alert_window_minutes = original_alert_window_minutes
