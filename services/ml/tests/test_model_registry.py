from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.features import PARENT_EDUCATION_LEVELS
from app.main import app
from app.model_store import (
    ModelBundle,
    active_version,
    list_versions,
    load_active,
    save_model,
    save_version,
    set_active,
    version_dir,
)
from training.dataset import TARGET, generate_dataset
from training.school import train_with_school_data

TOKEN = "test-admin-token"
EDUCATION = {code: name for name, code in PARENT_EDUCATION_LEVELS.items()}
BOOLEANS = ("home_internet", "has_study_device", "student_works")


def school_rows(n: int = 120, seed: int = 11) -> list[dict[str, Any]]:
    """Rows shaped like the ones the API sends, built from the synthetic generator."""
    rows = []
    for record in generate_dataset(n, seed).to_dict("records"):
        features = {name: value for name, value in record.items() if name != TARGET}
        features["parent_education"] = EDUCATION[int(features["parent_education"])]
        for name in BOOLEANS:
            features[name] = bool(features[name])
        for name in (
            "failed_subjects",
            "late_count",
            "behavior_rating",
            "study_hours_week",
            "family_communication",
            "household_size",
        ):
            features[name] = int(features[name])
        rows.append({"features": features, "dropout": bool(record[TARGET])})
    return rows


# --- Registro en disco -------------------------------------------------------------------


def test_versions_are_listed_and_one_is_active(trained_bundle: ModelBundle, tmp_path: Path) -> None:
    save_version(trained_bundle, tmp_path)

    assert [item["version"] for item in list_versions(tmp_path)] == [trained_bundle.version]
    assert active_version(tmp_path) is None
    set_active(tmp_path, trained_bundle.version)
    assert active_version(tmp_path) == trained_bundle.version


def test_a_single_legacy_model_becomes_the_first_version(
    trained_bundle: ModelBundle, tmp_path: Path
) -> None:
    save_model(trained_bundle, tmp_path)

    loaded = load_active(tmp_path)

    assert loaded is not None and loaded.version == trained_bundle.version
    assert active_version(tmp_path) == trained_bundle.version
    assert (version_dir(tmp_path, trained_bundle.version) / "model.joblib").exists()


def test_version_names_cannot_escape_the_registry(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        version_dir(tmp_path, "../outside")


# --- Entrenamiento con datos del colegio ---------------------------------------------------


def test_school_training_scores_on_held_out_real_cases() -> None:
    result = train_with_school_data(school_rows(), synthetic_samples=600)

    holdout = result.bundle.metadata["school_holdout"]
    assert result.bundle.version.endswith("-school")
    assert result.bundle.metadata["dataset"]["school_samples"] == 84
    assert holdout["cases"] == 36
    assert 0 <= holdout["recall"] <= 1


def test_school_training_needs_both_outcomes() -> None:
    rows = [row | {"dropout": False} for row in school_rows(30)]

    with pytest.raises(ValueError, match="of each outcome"):
        train_with_school_data(rows, synthetic_samples=600)


# --- Endpoints ---------------------------------------------------------------------------


@pytest.fixture
def admin_client(
    trained_bundle: ModelBundle, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    monkeypatch.setenv("ML_ADMIN_TOKEN", TOKEN)
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))
    get_settings.cache_clear()
    save_version(trained_bundle, tmp_path)
    app.state.model = set_active(tmp_path, trained_bundle.version)
    yield TestClient(app)
    app.state.model = None
    get_settings.cache_clear()


def test_admin_actions_require_the_token(admin_client: TestClient) -> None:
    assert admin_client.get("/v1/models").status_code == 403
    assert admin_client.get("/v1/models", headers={"X-Admin-Token": "wrong"}).status_code == 403


def test_train_stores_a_candidate_and_activation_switches_the_model(
    admin_client: TestClient, trained_bundle: ModelBundle
) -> None:
    headers = {"X-Admin-Token": TOKEN}

    trained = admin_client.post(
        "/v1/models/train", json={"rows": school_rows()}, headers=headers
    ).json()
    candidate = trained["candidate"]["version"]
    listed = admin_client.get("/v1/models", headers=headers).json()
    activated = admin_client.post(f"/v1/models/{candidate}/activate", headers=headers)
    rollback = admin_client.post(f"/v1/models/{trained_bundle.version}/activate", headers=headers)
    unknown = admin_client.post("/v1/models/nope/activate", headers=headers)

    assert trained["candidate"]["active"] is False
    assert trained["active_on_holdout"]["cases"] == trained["candidate"]["school_holdout"]["cases"]
    assert {item["version"]: item["active"] for item in listed} == {
        candidate: False,
        trained_bundle.version: True,
    }
    assert activated.json()["active"] is True
    assert rollback.json()["version"] == trained_bundle.version
    assert app.state.model.version == trained_bundle.version
    assert unknown.status_code == 404


def test_train_rejects_too_little_data(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/v1/models/train",
        json={"rows": school_rows(10)},
        headers={"X-Admin-Token": TOKEN},
    )

    assert response.status_code == 422
