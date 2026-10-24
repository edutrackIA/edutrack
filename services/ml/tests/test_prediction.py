from fastapi.testclient import TestClient

from app.features import FEATURE_NAMES


def test_predict_requires_a_loaded_model(client: TestClient, safe_features: dict) -> None:
    response = client.post("/v1/predict", json={"student_id": 1, "features": safe_features})

    assert response.status_code == 503


def test_model_info(client_with_model: TestClient) -> None:
    response = client_with_model.get("/v1/model")

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "RandomForestClassifier"
    assert set(body["features"]) <= set(FEATURE_NAMES)
    assert 0 <= body["metrics"]["roc_auc"] <= 1


def test_risky_profile_scores_higher_than_safe_profile(
    client_with_model: TestClient, at_risk_features: dict, safe_features: dict
) -> None:
    risky = client_with_model.post(
        "/v1/predict", json={"student_id": 1, "features": at_risk_features}
    ).json()
    safe = client_with_model.post(
        "/v1/predict", json={"student_id": 2, "features": safe_features}
    ).json()

    assert 0 <= safe["probability"] < risky["probability"] <= 1
    assert risky["model_version"].startswith("rf-")


def test_prediction_explains_top_factors(
    client_with_model: TestClient, at_risk_features: dict
) -> None:
    body = client_with_model.post(
        "/v1/predict", json={"student_id": 1, "features": at_risk_features}
    ).json()

    factors = body["top_factors"]
    assert 0 < len(factors) <= 5
    contributions = [factor["contribution"] for factor in factors]
    assert contributions == sorted(contributions, reverse=True)
    assert all(value > 0 for value in contributions)
    first = factors[0]
    assert first["value"] == at_risk_features[first["feature"]]


def test_batch_prediction_keeps_order(
    client_with_model: TestClient, at_risk_features: dict, safe_features: dict
) -> None:
    payload = {
        "items": [
            {"student_id": 10, "features": safe_features},
            {"student_id": 20, "features": at_risk_features},
        ]
    }

    body = client_with_model.post("/v1/predict/batch", json=payload).json()

    assert [item["student_id"] for item in body["items"]] == [10, 20]
    assert body["items"][0]["model_version"] == body["model_version"]


def test_invalid_features_are_rejected(client_with_model: TestClient, safe_features: dict) -> None:
    bad = {**safe_features, "attendance_rate": 1.5, "parent_education": "PHD"}

    response = client_with_model.post("/v1/predict", json={"student_id": 1, "features": bad})

    assert response.status_code == 422


def test_batch_cannot_be_empty(client_with_model: TestClient) -> None:
    response = client_with_model.post("/v1/predict/batch", json={"items": []})

    assert response.status_code == 422
