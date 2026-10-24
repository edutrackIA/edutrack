from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.model_store import ModelBundle
from training.train import train


@pytest.fixture(scope="session")
def trained_bundle() -> ModelBundle:
    return train(n_samples=600, seed=7, quick=True).bundle


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.state.model = None
    yield TestClient(app)
    app.state.model = None


@pytest.fixture
def client_with_model(trained_bundle: ModelBundle) -> Iterator[TestClient]:
    app.state.model = trained_bundle
    yield TestClient(app)
    app.state.model = None


@pytest.fixture
def at_risk_features() -> dict:
    return {
        "avg_score": 9.5,
        "failed_subjects": 4,
        "score_trend": -1.8,
        "attendance_rate": 0.78,
        "late_count": 9,
        "behavior_rating": 2,
        "study_hours_week": 2,
        "parent_education": "PRIMARY",
        "home_internet": False,
        "has_study_device": False,
        "family_communication": 2,
        "student_works": True,
        "household_size": 7,
    }


@pytest.fixture
def safe_features() -> dict:
    return {
        "avg_score": 17.5,
        "failed_subjects": 0,
        "score_trend": 1.2,
        "attendance_rate": 0.98,
        "late_count": 0,
        "behavior_rating": 5,
        "study_hours_week": 15,
        "parent_education": "UNIVERSITY",
        "home_internet": True,
        "has_study_device": True,
        "family_communication": 5,
        "student_works": False,
        "household_size": 4,
    }
