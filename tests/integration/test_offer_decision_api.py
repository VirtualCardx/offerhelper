from fastapi.testclient import TestClient


def test_offer_recommendation_api(client: TestClient) -> None:
    response = client.post(
        "/api/v1/offers/recommend",
        json={
            "candidate": {
                "currentSalary": 30000,
                "yearsExperience": 5,
                "level": "P6",
                "interviewScore": 90,
                "hasOtherOffer": True,
            },
            "market": {
                "P50": 35000,
                "P75": 45000,
            },
            "budget": {
                "limit": 40000,
            },
            "factors": [
                {"factorCode": "company", "weight": 0.3, "min": 0.8, "target": 1.0, "max": 1.1},
                {"factorCode": "domain", "weight": 0.3, "min": 0.9, "target": 1.05, "max": 1.2},
                {"factorCode": "department", "weight": 0.2, "min": 0.95, "target": 1.0, "max": 1.15},
                {"factorCode": "talent", "weight": 0.2, "min": 1.0, "target": 1.15, "max": 1.3},
            ],
            "selectedPoint": "target",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendedOffer"] == "39501.00"
    assert payload["crValue"] == "1.0450"
    assert payload["riskLevel"] == "YELLOW"
    assert "salary_increase_over_30_percent" in payload["riskReasons"]
