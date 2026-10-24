import json
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import BadGatewayError
from app.domain import (
    AcademicPeriod,
    Attendance,
    AttendanceStatus,
    BehaviorRecord,
    FamilySurvey,
    Grade,
    ParentEducation,
    RiskAssessment,
    Student,
)
from app.main import app
from app.services.risk.features import FeatureBuilder
from app.services.risk.ml_client import HttpMlClient, get_ml_client
from tests.conftest import School, auth

RUN_URL = "/api/v1/risk-assessments/run"
THRESHOLDS_URL = "/api/v1/settings/risk-thresholds"


class FakeMlClient:
    """Deterministic stand-in for the ML service: lower averages mean higher risk."""

    version = "rf-test"

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []

    def predict_batch(self, items: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        self.calls.append(items)
        predictions = []
        for item in items:
            average = item["features"]["avg_score"]
            probability = round(max(0.0, min(1.0, (16 - average) / 8)), 4)
            predictions.append(
                {
                    "student_id": item["student_id"],
                    "probability": probability,
                    "model_version": self.version,
                    "top_factors": [
                        {"feature": "avg_score", "value": average, "contribution": 0.3}
                    ],
                }
            )
        return self.version, predictions


class FailingMlClient:
    def predict_batch(self, items: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        raise BadGatewayError("The ML service is not available")


@pytest.fixture
def fake_ml() -> Iterator[FakeMlClient]:
    fake = FakeMlClient()
    app.dependency_overrides[get_ml_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_ml_client, None)


def add_records(
    db: Session,
    school: School,
    student: Student,
    scores: list[float],
    *,
    absences: int = 0,
    lates: int = 0,
    survey: bool = True,
    period: AcademicPeriod | None = None,
) -> None:
    period = period or school.period
    subjects = [school.math, school.language]
    for subject, score in zip(subjects, scores, strict=False):
        db.add(
            Grade(student_id=student.id, subject_id=subject.id, period_id=period.id, score=score)
        )
    statuses = (
        [AttendanceStatus.ABSENT] * absences
        + [AttendanceStatus.LATE] * lates
        + [AttendanceStatus.PRESENT] * (10 - absences - lates)
    )
    db.add_all(
        Attendance(student_id=student.id, date=period.start_date + timedelta(days=i), status=s)
        for i, s in enumerate(statuses)
    )
    if survey:
        db.add(
            FamilySurvey(
                student_id=student.id,
                period_id=period.id,
                responder_id=school.analyst.id,
                study_hours_week=6,
                parent_education=ParentEducation.SECONDARY,
                home_internet=True,
                has_study_device=False,
                family_communication=3,
                student_works=False,
                household_size=5,
            )
        )
    db.commit()


@pytest.fixture
def evaluated_school(school: School, db_session: Session) -> School:
    add_records(db_session, school, school.student_a, [8, 10], absences=3, lates=1)  # high
    add_records(db_session, school, school.student_a2, [17, 18])  # low
    add_records(db_session, school, school.student_b, [12, 13], survey=False)  # skipped
    return school


# --- Construcción de variables ---------------------------------------------


def test_feature_builder_computes_features(evaluated_school: School, db_session: Session) -> None:
    school = evaluated_school
    db_session.add(
        BehaviorRecord(student_id=school.student_a.id, period_id=school.period.id, rating=2)
    )
    db_session.commit()

    result = FeatureBuilder(db_session).build(school.student_a, school.period)

    assert result.missing is None
    assert result.features == {
        "avg_score": 9.0,
        "failed_subjects": 2,
        "score_trend": 0.0,
        "attendance_rate": 0.7,
        "late_count": 1,
        "behavior_rating": 2,
        "study_hours_week": 6,
        "parent_education": "SECONDARY",
        "home_internet": True,
        "has_study_device": False,
        "family_communication": 3,
        "student_works": False,
        "household_size": 5,
    }


def test_feature_builder_uses_previous_period_for_trend(
    school: School, db_session: Session
) -> None:
    second = AcademicPeriod(
        institution_id=school.period.institution_id,
        year=2026,
        bimester=2,
        start_date=date(2026, 5, 18),
        end_date=date(2026, 7, 17),
    )
    db_session.add(second)
    db_session.commit()
    add_records(db_session, school, school.student_a, [10, 12])
    add_records(db_session, school, school.student_a, [14, 16], survey=False, period=second)

    features = FeatureBuilder(db_session).build(school.student_a, second).features

    assert features is not None
    assert features["score_trend"] == 4.0
    assert features["behavior_rating"] == 3


@pytest.mark.parametrize(
    ("grades", "attendance", "survey", "reason"),
    [
        (False, True, True, "No grades for the period"),
        (True, False, True, "No attendance for the period"),
        (True, True, False, "No family survey"),
    ],
)
def test_feature_builder_reports_missing_data(
    school: School,
    db_session: Session,
    grades: bool,
    attendance: bool,
    survey: bool,
    reason: str,
) -> None:
    student = school.student_a
    add_records(db_session, school, student, [12, 12] if grades else [], survey=survey)
    if not attendance:
        db_session.query(Attendance).delete()
        db_session.commit()

    assert FeatureBuilder(db_session).build(student, school.period).missing == reason


# --- Ejecución -------------------------------------------------------------


def test_analyst_runs_assessment(
    client: TestClient, evaluated_school: School, fake_ml: FakeMlClient
) -> None:
    school = evaluated_school

    response = client.post(
        RUN_URL, json={"period_id": school.period.id}, headers=auth(school.analyst)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["evaluated"] == 2
    assert body["skipped"] == 1
    assert body["model_version"] == "rf-test"
    assert body["by_level"] == {"LOW": 1, "MEDIUM": 0, "HIGH": 1}
    reasons = {item["student_id"]: item["reason"] for item in body["skipped_students"]}
    assert reasons[school.student_b.id] == "No family survey"


def test_rerun_updates_instead_of_duplicating(
    client: TestClient, evaluated_school: School, fake_ml: FakeMlClient, db_session: Session
) -> None:
    school = evaluated_school
    payload = {"period_id": school.period.id, "classroom_id": school.classroom_a.id}

    client.post(RUN_URL, json=payload, headers=auth(school.analyst))
    client.post(RUN_URL, json=payload, headers=auth(school.analyst))

    assert db_session.scalar(select(func.count()).select_from(RiskAssessment)) == 2
    assert [item["student_id"] for item in fake_ml.calls[-1]] == [
        school.student_a.id,
        school.student_a2.id,
    ]


def test_thresholds_change_assigned_levels(
    client: TestClient, evaluated_school: School, fake_ml: FakeMlClient
) -> None:
    school = evaluated_school
    client.put(
        THRESHOLDS_URL,
        json={"medium_from": 0.05, "high_from": 0.95},
        headers=auth(school.analyst),
    )

    body = client.post(
        RUN_URL, json={"period_id": school.period.id}, headers=auth(school.analyst)
    ).json()

    assert body["by_level"] == {"LOW": 1, "MEDIUM": 1, "HIGH": 0}


def test_run_without_evaluable_students(
    client: TestClient, school: School, fake_ml: FakeMlClient
) -> None:
    body = client.post(
        RUN_URL, json={"period_id": school.period.id}, headers=auth(school.analyst)
    ).json()

    assert body["evaluated"] == 0
    assert body["model_version"] is None
    assert fake_ml.calls == []


def test_run_validates_period_classroom_and_role(
    client: TestClient, evaluated_school: School, fake_ml: FakeMlClient
) -> None:
    school = evaluated_school

    foreign_period = client.post(
        RUN_URL, json={"period_id": school.foreign_period.id}, headers=auth(school.analyst)
    )
    foreign_classroom = client.post(
        RUN_URL,
        json={"period_id": school.period.id, "classroom_id": school.foreign_classroom.id},
        headers=auth(school.analyst),
    )
    teacher = client.post(
        RUN_URL, json={"period_id": school.period.id}, headers=auth(school.teacher)
    )

    assert foreign_period.status_code == 422
    assert foreign_classroom.status_code == 422
    assert teacher.status_code == 403


def test_run_reports_ml_service_errors(client: TestClient, evaluated_school: School) -> None:
    app.dependency_overrides[get_ml_client] = FailingMlClient
    try:
        response = client.post(
            RUN_URL,
            json={"period_id": evaluated_school.period.id},
            headers=auth(evaluated_school.analyst),
        )
    finally:
        app.dependency_overrides.pop(get_ml_client, None)

    assert response.status_code == 502
    assert response.json()["code"] == "ML_SERVICE_UNAVAILABLE"


# --- Visibilidad -----------------------------------------------------------


@pytest.fixture
def assessed_school(client: TestClient, evaluated_school: School, fake_ml: FakeMlClient) -> School:
    school = evaluated_school
    client.post(RUN_URL, json={"period_id": school.period.id}, headers=auth(school.analyst))
    return school


def test_staff_see_risk_in_student_record_and_lists(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school

    record = client.get(f"/api/v1/students/{school.student_a.id}", headers=auth(school.teacher))
    listing = client.get(
        f"/api/v1/classrooms/{school.classroom_a.id}/students?level=HIGH",
        headers=auth(school.teacher),
    )

    latest = record.json()["latest_risk"]
    assert latest["level"] == "HIGH"
    assert latest["top_factors"][0]["label"] == "Promedio"
    assert [item["code"] for item in listing.json()] == ["A001"]
    assert listing.json()[0]["risk_level"] == "HIGH"


def test_parents_never_see_risk(client: TestClient, assessed_school: School) -> None:
    school = assessed_school
    headers = auth(school.parent)

    record = client.get(f"/api/v1/students/{school.student_a.id}", headers=headers)
    children = client.get("/api/v1/me/children", headers=headers)
    history = client.get(f"/api/v1/students/{school.student_a.id}/risk", headers=headers)

    assert record.json()["latest_risk"] is None
    assert children.json()[0]["risk_level"] is None
    assert history.status_code == 403


def test_risk_history(client: TestClient, assessed_school: School) -> None:
    school = assessed_school

    response = client.get(
        f"/api/v1/students/{school.student_a.id}/risk", headers=auth(school.director)
    )
    missing = client.get("/api/v1/students/9999/risk", headers=auth(school.director))

    assert len(response.json()) == 1
    assert response.json()[0]["model_version"] == "rf-test"
    assert missing.status_code == 404


# --- Umbrales --------------------------------------------------------------


def test_thresholds_default_and_update(client: TestClient, school: School) -> None:
    default = client.get(THRESHOLDS_URL, headers=auth(school.director))
    updated = client.put(
        THRESHOLDS_URL, json={"medium_from": 0.3, "high_from": 0.6}, headers=auth(school.analyst)
    )
    again = client.put(
        THRESHOLDS_URL, json={"medium_from": 0.35, "high_from": 0.65}, headers=auth(school.analyst)
    )

    assert default.json() == {"medium_from": 0.4, "high_from": 0.7}
    assert updated.json() == {"medium_from": 0.3, "high_from": 0.6}
    assert client.get(THRESHOLDS_URL, headers=auth(school.director)).json() == again.json()


def test_thresholds_validation_and_roles(client: TestClient, school: School) -> None:
    inverted = client.put(
        THRESHOLDS_URL, json={"medium_from": 0.8, "high_from": 0.5}, headers=auth(school.analyst)
    )
    director = client.put(
        THRESHOLDS_URL, json={"medium_from": 0.3, "high_from": 0.6}, headers=auth(school.director)
    )
    teacher = client.get(THRESHOLDS_URL, headers=auth(school.teacher))

    assert inverted.status_code == 422
    assert director.status_code == 403
    assert teacher.status_code == 403


# --- Cliente HTTP ----------------------------------------------------------


def test_http_ml_client_sends_batches() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        items = json.loads(request.content)["items"]
        return httpx.Response(
            200,
            json={
                "model_version": "rf-x",
                "items": [{"student_id": i["student_id"], "probability": 0.1} for i in items],
            },
        )

    client = HttpMlClient("http://ml", transport=httpx.MockTransport(handler))
    items = [{"student_id": n, "features": {}} for n in range(3)]

    version, predictions = client.predict_batch(items)

    assert version == "rf-x"
    assert [p["student_id"] for p in predictions] == [0, 1, 2]


def test_http_ml_client_wraps_errors() -> None:
    client = HttpMlClient(
        "http://ml", transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )

    with pytest.raises(BadGatewayError):
        client.predict_batch([{"student_id": 1, "features": {}}])
