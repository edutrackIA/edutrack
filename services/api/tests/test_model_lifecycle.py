from collections.abc import Iterator
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_school_today
from app.core.errors import NotFoundError
from app.domain import ExitReason, RiskAssessment, RiskLevel, StudentStatus
from app.main import app
from app.services import model_lifecycle_service
from app.services.risk.model_registry import get_model_registry
from tests.conftest import School, auth


class FakeRegistry:
    """In-memory stand-in for the ML service's model registry."""

    def __init__(self) -> None:
        self.models: list[dict[str, Any]] = [
            {
                "version": "rf-base",
                "trained_at": "2026-10-25T00:00:00",
                "active": True,
                "dataset": {"n_samples": 4000},
            },
        ]
        self.trained_rows: list[dict[str, Any]] = []

    def versions(self) -> list[dict[str, Any]]:
        return self.models

    def train(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        self.trained_rows = rows
        candidate = {
            "version": "rf-school",
            "trained_at": "2026-12-01T10:00:00",
            "active": False,
            "dataset": {
                "synthetic_samples": 4000,
                "school_samples": len(rows),
                "school_dropouts": 1,
            },
            "school_holdout": {"cases": 30, "recall": 0.8, "precision": 0.5},
        }
        self.models.append(candidate)
        return {"candidate": candidate, "active_on_holdout": {"cases": 30, "recall": 0.6}}

    def activate(self, version: str) -> dict[str, Any]:
        if version not in {item["version"] for item in self.models}:
            raise NotFoundError("Unknown model version")
        for item in self.models:
            item["active"] = item["version"] == version
        return next(item for item in self.models if item["version"] == version)


@pytest.fixture
def registry() -> Iterator[FakeRegistry]:
    fake = FakeRegistry()
    app.dependency_overrides[get_model_registry] = lambda: fake
    app.dependency_overrides[get_school_today] = lambda: date(2026, 12, 1)
    yield fake
    app.dependency_overrides.pop(get_model_registry, None)
    app.dependency_overrides.pop(get_school_today, None)


@pytest.fixture
def known_outcome(evaluated_school: School, db_session: Session) -> School:
    """One assessed student who later dropped out: a real, labeled case."""
    school = evaluated_school
    school.student_a.status = StudentStatus.WITHDRAWN
    school.student_a.exit_date = date(2026, 6, 1)
    school.student_a.exit_reason = ExitReason.WORK
    db_session.add(
        RiskAssessment(
            student_id=school.student_a.id,
            period_id=school.period.id,
            probability=0.9,
            level=RiskLevel.HIGH,
            model_version="rf-base",
            top_factors=[],
        )
    )
    db_session.commit()
    return school


def test_overview_lists_versions_and_training_readiness(
    client: TestClient, school: School, registry: FakeRegistry
) -> None:
    body = client.get("/api/v1/models", headers=auth(school.director)).json()

    assert [(v["version"], v["active"]) for v in body["versions"]] == [("rf-base", True)]
    assert body["versions"][0]["synthetic_samples"] == 4000
    assert body["training"] == {
        "labeled": 0,
        "dropouts": 0,
        "min_labeled": 200,
        "min_dropouts": 20,
        "can_train": False,
    }


def test_training_needs_enough_real_outcomes(
    client: TestClient, school: School, registry: FakeRegistry
) -> None:
    response = client.post("/api/v1/models/train", headers=auth(school.analyst))

    assert response.status_code == 422
    assert response.json()["code"] == "NOT_ENOUGH_DATA"
    assert "hay 0 y 0" in response.json()["message"]


def test_analysis_trains_and_direction_activates(
    client: TestClient,
    known_outcome: School,
    registry: FakeRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    school = known_outcome
    monkeypatch.setattr(model_lifecycle_service, "MIN_TRAINING_ROWS", 1)
    monkeypatch.setattr(model_lifecycle_service, "MIN_TRAINING_DROPOUTS", 1)

    director_train = client.post("/api/v1/models/train", headers=auth(school.director))
    trained = client.post("/api/v1/models/train", headers=auth(school.analyst)).json()
    analyst_activate = client.post(
        "/api/v1/models/rf-school/activation", headers=auth(school.analyst)
    )
    activated = client.post(
        "/api/v1/models/rf-school/activation", headers=auth(school.director)
    ).json()
    rollback = client.post("/api/v1/models/rf-base/activation", headers=auth(school.director))
    unknown = client.post("/api/v1/models/nope/activation", headers=auth(school.director))

    assert director_train.status_code == 403
    assert trained["candidate"]["active"] is False
    assert trained["candidate"]["trained_by"] == school.analyst.full_name
    assert trained["active_on_holdout"]["recall"] == 0.6
    assert registry.trained_rows == [
        {"features": registry.trained_rows[0]["features"], "dropout": True}
    ]
    assert "student_id" not in registry.trained_rows[0]["features"]
    assert analyst_activate.status_code == 403
    assert activated["active"] is True
    assert activated["activated_by"] == school.director.full_name
    assert rollback.json()["version"] == "rf-base"
    assert unknown.status_code == 404
