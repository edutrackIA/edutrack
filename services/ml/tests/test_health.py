from fastapi.testclient import TestClient


def test_health_reports_model_not_loaded(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": False}


def test_health_reports_model_loaded(client_with_model: TestClient) -> None:
    assert client_with_model.get("/health").json()["model_loaded"] is True
