from __future__ import annotations

import pickle
from pathlib import Path

from fastapi.testclient import TestClient

from src.modules.acceptance_prediction.domain.services import WeightedProbabilityModel


def test_create_and_get_candidate(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    create_response = client.post(
        "/api/v1/candidates",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "name": "Alice",
            "currentSalary": 30000,
            "expectedSalary": 38000,
            "yearsExperience": 5,
            "level": "P6",
            "skills": ["Growth", "SQL", "CRM"],
            "interviewScore": 90,
            "hasOtherOffer": True,
            "city": "Shanghai",
        },
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["name"] == "Alice"
    assert payload["skills"] == ["Growth", "SQL", "CRM"]

    get_response = client.get(f"/api/v1/candidates/{payload['id']}")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["currentSalary"] == "30000.00"
    assert get_payload["positionId"] == reference_ids["position_id"]


def test_list_org_and_candidate_resources(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    company_response = client.get("/api/v1/org/companies")
    assert company_response.status_code == 200
    company_payload = company_response.json()
    assert len(company_payload) == 1
    assert company_payload[0]["id"] == reference_ids["company_id"]

    department_response = client.get(
        "/api/v1/org/departments",
        params={"companyId": reference_ids["company_id"]},
    )
    assert department_response.status_code == 200
    department_payload = department_response.json()
    assert len(department_payload) == 1
    assert department_payload[0]["id"] == reference_ids["department_id"]

    position_response = client.get(
        "/api/v1/org/positions",
        params={"companyId": reference_ids["company_id"]},
    )
    assert position_response.status_code == 200
    position_payload = position_response.json()
    assert len(position_payload) == 1
    assert position_payload[0]["id"] == reference_ids["position_id"]

    create_candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "name": "Filterable Candidate",
            "currentSalary": 28000,
            "expectedSalary": 34000,
            "yearsExperience": 4,
            "level": "P5",
            "skills": ["SQL", "Analytics"],
            "interviewScore": 86,
            "hasOtherOffer": False,
            "city": "Shanghai",
        },
    )
    assert create_candidate_response.status_code == 200

    candidates_response = client.get(
        "/api/v1/candidates",
        params={"companyId": reference_ids["company_id"], "limit": 20},
    )
    assert candidates_response.status_code == 200
    candidates_payload = candidates_response.json()
    assert len(candidates_payload) == 1
    assert candidates_payload[0]["name"] == "Filterable Candidate"


def test_create_and_get_market_salary(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    create_response = client.post(
        "/api/v1/market-salary",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 25000,
            "P50": 35000,
            "P75": 45000,
            "source": "manual-test",
        },
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["P50"] == "35000.00"

    get_response = client.get(
        "/api/v1/market-salary",
        params={"positionId": reference_ids["position_id"], "city": "Shanghai"},
    )
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["P75"] == "45000.00"
    assert get_payload["source"] == "manual-test"


def test_get_market_salary_returns_latest_snapshot_when_duplicates_exist(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    first_response = client.post(
        "/api/v1/market-salary",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 24000,
            "P50": 34000,
            "P75": 43000,
            "source": "manual-initial",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/market-salary",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 25500,
            "P50": 36500,
            "P75": 47000,
            "source": "manual-latest",
        },
    )
    assert second_response.status_code == 200

    get_response = client.get(
        "/api/v1/market-salary",
        params={"positionId": reference_ids["position_id"], "city": "Shanghai"},
    )

    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["id"] == second_response.json()["id"]
    assert payload["P50"] == "36500.00"
    assert payload["source"] == "manual-latest"

    history_response = client.get(
        "/api/v1/market-salary/history",
        params={"positionId": reference_ids["position_id"], "city": "Shanghai", "limit": 10},
    )
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert len(history_payload) == 2
    assert history_payload[0]["id"] == second_response.json()["id"]
    assert history_payload[1]["id"] == first_response.json()["id"]

    promote_response = client.post(f"/api/v1/market-salary/{first_response.json()['id']}/promote")
    assert promote_response.status_code == 200
    promoted_payload = promote_response.json()
    assert promoted_payload["id"] != first_response.json()["id"]
    assert promoted_payload["P50"] == "34000.00"
    assert promoted_payload["source"] == "manual-initial"

    latest_after_promote = client.get(
        "/api/v1/market-salary",
        params={"positionId": reference_ids["position_id"], "city": "Shanghai"},
    )
    assert latest_after_promote.status_code == 200
    assert latest_after_promote.json()["id"] == promoted_payload["id"]

    history_after_promote = client.get(
        "/api/v1/market-salary/history",
        params={"positionId": reference_ids["position_id"], "city": "Shanghai", "limit": 10},
    )
    assert history_after_promote.status_code == 200
    promoted_history_payload = history_after_promote.json()
    assert len(promoted_history_payload) == 3
    assert promoted_history_payload[0]["id"] == promoted_payload["id"]
    assert promoted_history_payload[1]["id"] == second_response.json()["id"]


def test_update_and_delete_data_hub_resources(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    market_response = client.post(
        "/api/v1/market-salary",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 25000,
            "P50": 35000,
            "P75": 45000,
            "source": "manual-test",
        },
    )
    assert market_response.status_code == 200
    market_id = market_response.json()["id"]

    update_market_response = client.patch(
        f"/api/v1/market-salary/{market_id}",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 26000,
            "P50": 36500,
            "P75": 47000,
            "source": "manual-updated",
        },
    )
    assert update_market_response.status_code == 200
    assert update_market_response.json()["P50"] == "36500.00"

    salary_response = client.post(
        "/api/v1/employee-salary",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "level": "P6",
            "salary": 36000,
        },
    )
    assert salary_response.status_code == 200
    salary_id = salary_response.json()["id"]

    update_salary_response = client.patch(
        f"/api/v1/employee-salary/{salary_id}",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "level": "P7",
            "salary": 39000,
        },
    )
    assert update_salary_response.status_code == 200
    assert update_salary_response.json()["level"] == "P7"
    assert update_salary_response.json()["salary"] == "39000.00"

    strategy_response = client.post(
        "/api/v1/compensation-strategies",
        json={
            "companyId": reference_ids["company_id"],
            "name": "Editable Strategy",
            "budgetPolicy": {
                "limit": 40000,
                "yellowThreshold": 1.0,
                "redThreshold": 1.1,
            },
            "factors": [
                {"factorCode": "company", "weight": 0.3, "min": 0.8, "target": 1.0, "max": 1.1},
                {"factorCode": "domain", "weight": 0.3, "min": 0.9, "target": 1.05, "max": 1.2},
                {"factorCode": "department", "weight": 0.2, "min": 0.95, "target": 1.0, "max": 1.15},
                {"factorCode": "talent", "weight": 0.2, "min": 1.0, "target": 1.15, "max": 1.3},
            ],
        },
    )
    assert strategy_response.status_code == 200
    strategy_id = strategy_response.json()["id"]

    update_strategy_response = client.patch(
        f"/api/v1/compensation-strategies/{strategy_id}",
        json={
            "name": "Editable Strategy Updated",
            "budgetPolicy": {
                "limit": 45000,
                "yellowThreshold": 1.05,
                "redThreshold": 1.15,
            },
            "factors": [
                {"factorCode": "company", "weight": 0.25, "min": 0.8, "target": 1.0, "max": 1.1},
                {"factorCode": "domain", "weight": 0.35, "min": 0.9, "target": 1.05, "max": 1.2},
                {"factorCode": "department", "weight": 0.2, "min": 0.95, "target": 1.0, "max": 1.15},
                {"factorCode": "talent", "weight": 0.2, "min": 1.0, "target": 1.15, "max": 1.3},
            ],
        },
    )
    assert update_strategy_response.status_code == 200
    strategy_payload = update_strategy_response.json()
    assert strategy_payload["name"] == "Editable Strategy Updated"
    assert strategy_payload["budgetPolicy"]["limit"] == "45000"
    assert strategy_payload["factors"][0]["weight"] == "0.2500"

    delete_strategy_response = client.delete(f"/api/v1/compensation-strategies/{strategy_id}")
    assert delete_strategy_response.status_code == 204

    delete_salary_response = client.delete(f"/api/v1/employee-salary/{salary_id}")
    assert delete_salary_response.status_code == 204

    delete_market_response = client.delete(f"/api/v1/market-salary/{market_id}")
    assert delete_market_response.status_code == 204


def test_offer_recommendation_by_candidate(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "name": "Bob",
            "currentSalary": 30000,
            "expectedSalary": 40000,
            "yearsExperience": 6,
            "level": "P6",
            "skills": ["Growth", "SQL"],
            "interviewScore": 92,
            "hasOtherOffer": True,
            "city": "Shanghai",
        },
    )
    candidate_id = candidate_response.json()["id"]

    market_response = client.post(
        "/api/v1/market-salary",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 25000,
            "P50": 35000,
            "P75": 45000,
            "source": "manual-test",
        },
    )
    assert market_response.status_code == 200

    offer_response = client.post(
        "/api/v1/offers/recommend/by-candidate",
        json={
            "candidateId": candidate_id,
            "budget": {"limit": 40000},
            "factors": [
                {"factorCode": "company", "weight": 0.3, "min": 0.8, "target": 1.0, "max": 1.1},
                {"factorCode": "domain", "weight": 0.3, "min": 0.9, "target": 1.05, "max": 1.2},
                {"factorCode": "department", "weight": 0.2, "min": 0.95, "target": 1.0, "max": 1.15},
                {"factorCode": "talent", "weight": 0.2, "min": 1.0, "target": 1.15, "max": 1.3},
            ],
            "selectedPoint": "target",
        },
    )

    assert offer_response.status_code == 200
    payload = offer_response.json()
    assert payload["recommendedOffer"] == "39501.00"
    assert payload["riskLevel"] == "YELLOW"


def test_create_strategy_and_persist_offer(client: TestClient) -> None:
    reference_ids = client.app.state.test_ids
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

    register_model_response = client.post(
        "/api/v1/models/register",
        json={
            "modelName": "baseline-offer-acceptance",
            "modelVersion": "0.3.0",
            "framework": "xgboost",
            "artifactUri": artifact_uri,
            "config": {
                "base_probability": "0.30",
                "offer_market_bonus": "0.01",
                "raise_bonus": "0.01",
                "high_score_bonus": "0.01",
                "medium_score_bonus": "0.01",
                "competing_offer_penalty": "0.01",
            },
            "metrics": {"auc": 0.86},
            "activate": True,
        },
    )
    assert register_model_response.status_code == 200

    salary_response_1 = client.post(
        "/api/v1/employee-salary",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "level": "P6",
            "salary": 35000,
        },
    )
    salary_response_2 = client.post(
        "/api/v1/employee-salary",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "level": "P6",
            "salary": 37000,
        },
    )
    assert salary_response_1.status_code == 200
    assert salary_response_2.status_code == 200

    candidate_response = client.post(
        "/api/v1/candidates",
        json={
            "companyId": reference_ids["company_id"],
            "departmentId": reference_ids["department_id"],
            "positionId": reference_ids["position_id"],
            "name": "Cindy",
            "currentSalary": 30000,
            "expectedSalary": 42000,
            "yearsExperience": 7,
            "level": "P6",
            "skills": ["Growth", "SQL", "CRM"],
            "interviewScore": 95,
            "hasOtherOffer": True,
            "city": "Shanghai",
        },
    )
    candidate_id = candidate_response.json()["id"]

    market_response = client.post(
        "/api/v1/market-salary",
        json={
            "positionId": reference_ids["position_id"],
            "city": "Shanghai",
            "P25": 25000,
            "P50": 35000,
            "P75": 45000,
            "source": "manual-test",
        },
    )
    assert market_response.status_code == 200

    strategy_response = client.post(
        "/api/v1/compensation-strategies",
        json={
            "companyId": reference_ids["company_id"],
            "name": "Default 2026 Strategy",
            "budgetPolicy": {
                "limit": 40000,
                "yellowThreshold": 1.0,
                "redThreshold": 1.1,
            },
            "factors": [
                {"factorCode": "company", "weight": 0.3, "min": 0.8, "target": 1.0, "max": 1.1},
                {"factorCode": "domain", "weight": 0.3, "min": 0.9, "target": 1.05, "max": 1.2},
                {"factorCode": "department", "weight": 0.2, "min": 0.95, "target": 1.0, "max": 1.15},
                {"factorCode": "talent", "weight": 0.2, "min": 1.0, "target": 1.15, "max": 1.3},
            ],
        },
    )
    assert strategy_response.status_code == 200
    strategy_id = strategy_response.json()["id"]

    strategies_response = client.get(
        "/api/v1/compensation-strategies",
        params={"companyId": reference_ids["company_id"], "limit": 20},
    )
    assert strategies_response.status_code == 200
    strategies_payload = strategies_response.json()
    assert len(strategies_payload) == 1
    assert strategies_payload[0]["id"] == strategy_id

    offer_response = client.post(
        "/api/v1/offers/recommend-and-save",
        json={
            "candidateId": candidate_id,
            "strategyId": strategy_id,
            "selectedPoint": "target",
        },
    )

    assert offer_response.status_code == 200
    payload = offer_response.json()
    assert payload["offerId"]
    assert payload["candidateId"] == candidate_id
    assert payload["marketSnapshotId"]
    assert payload["strategyId"] == strategy_id
    assert payload["recommendedOffer"] == "39501.00"
    assert payload["acceptProbability"] == "0.81"
    assert payload["acceptanceModelVersion"] == "0.3.0"
    assert payload["budget"]["usageRatio"] == "0.9875"
    assert payload["budget"]["riskLevel"] == "LOW"
    assert payload["equity"]["riskLevel"] == "RED"
    assert payload["equity"]["inversionDetected"] is True
    assert payload["riskLevel"] == "RED"
    assert payload["outcomeStatus"] == "PENDING"
    assert payload["decidedAt"] is None

    detail_response = client.get(f"/api/v1/offers/{payload['offerId']}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["marketSnapshotId"] == payload["marketSnapshotId"]
    assert detail_payload["equity"]["P50"] == "36000.00"
    assert detail_payload["reportMarkdown"] is None
    assert detail_payload["acceptanceModelVersion"] == "0.3.0"

    outcome_response = client.post(
        f"/api/v1/offers/{payload['offerId']}/outcome",
        json={
            "outcomeStatus": "ACCEPTED",
            "outcomeNotes": "candidate signed the offer",
        },
    )
    assert outcome_response.status_code == 200
    outcome_payload = outcome_response.json()
    assert outcome_payload["outcomeStatus"] == "ACCEPTED"
    assert outcome_payload["outcomeNotes"] == "candidate signed the offer"
    assert outcome_payload["decidedAt"] is not None

    report_response = client.post(f"/api/v1/reports/offers/{payload['offerId']}/generate")
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["format"] == "markdown"
    assert "Offer Recommendation Report" in report_payload["content"]

    detail_after_report = client.get(f"/api/v1/offers/{payload['offerId']}")
    assert detail_after_report.status_code == 200
    assert "Offer Recommendation Report" in detail_after_report.json()["reportMarkdown"]

    list_response = client.get("/api/v1/offers", params={"candidateId": candidate_id, "riskLevel": "RED"})
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert len(list_payload) == 1
    assert list_payload[0]["offerId"] == payload["offerId"]
    assert list_payload[0]["marketSnapshotId"] == payload["marketSnapshotId"]
    assert list_payload[0]["outcomeStatus"] == "ACCEPTED"
