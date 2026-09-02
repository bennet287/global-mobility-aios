from __future__ import annotations

from fastapi.testclient import TestClient


def test_generate_training_cases(client: TestClient) -> None:
    response = client.post("/api/v1/training-cases/generate", json={"count": 3, "country": "Germany"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(case["country"] == "Germany" for case in data)
    assert all(case["scenario_json"] for case in data)


def test_list_training_cases(client: TestClient) -> None:
    client.post("/api/v1/training-cases/generate", json={"count": 2, "profession": "Registered Nurse"})
    response = client.get("/api/v1/training-cases?profession=Registered+Nurse")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert all(case["profession"] == "Registered Nurse" for case in data)


def test_run_training_case(client: TestClient) -> None:
    generate_response = client.post("/api/v1/training-cases/generate", json={"count": 1})
    case = generate_response.json()[0]

    response = client.post(f"/api/v1/training-cases/{case['id']}/run")
    assert response.status_code == 200
    data = response.json()
    assert data["coach_agent_name"] == "eligibility_coach"
    assert data["target_agent_name"] == "training_simulated_agent"
    assert data["status"] == "pending"
