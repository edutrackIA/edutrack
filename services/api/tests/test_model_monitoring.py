from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_school_today
from app.domain import (
    ExitReason,
    RiskAssessment,
    RiskLevel,
    Sex,
    Student,
    StudentStatus,
)
from app.main import app
from tests.conftest import School, auth

URL = "/api/v1/model-performance"
# school.period ends 2026-05-08: outcomes are known after 2026-11-04.
BEFORE_WINDOW = date(2026, 10, 28)
AFTER_WINDOW = date(2026, 12, 1)


@pytest.fixture
def today() -> Iterator[list[date]]:
    current = [AFTER_WINDOW]
    app.dependency_overrides[get_school_today] = lambda: current[0]
    yield current
    app.dependency_overrides.pop(get_school_today, None)


def add_case(
    db: Session,
    school: School,
    index: int,
    level: RiskLevel,
    status: StudentStatus = StudentStatus.ENROLLED,
) -> Student:
    student = Student(
        institution_id=school.classroom_a.institution_id,
        classroom_id=school.classroom_a.id,
        code=f"M{index:03d}",
        first_name=f"Alumno{index}",
        last_name="Prueba",
        birth_date=date(2012, 1, 1),
        sex=Sex.M,
        status=status,
    )
    if status == StudentStatus.WITHDRAWN:
        student.exit_date, student.exit_reason = date(2026, 6, 15), ExitReason.WORK
    if status == StudentStatus.TRANSFERRED:
        student.exit_date, student.exit_reason = date(2026, 6, 15), ExitReason.TRANSFER
    db.add(student)
    db.flush()
    db.add(
        RiskAssessment(
            student_id=student.id,
            period_id=school.period.id,
            probability={RiskLevel.HIGH: 0.9, RiskLevel.MEDIUM: 0.5, RiskLevel.LOW: 0.1}[level],
            level=level,
            model_version="rf-test",
            top_factors=[],
        )
    )
    return student


@pytest.fixture
def outcomes(db_session: Session, school: School) -> School:
    """4 dropouts (3 alerted), 16 students still enrolled (2 alerted), 1 transfer."""
    levels = [RiskLevel.HIGH, RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]
    for index, level in enumerate(levels):
        add_case(db_session, school, index, level, StudentStatus.WITHDRAWN)
    for index in range(4, 20):
        level = RiskLevel.MEDIUM if index < 6 else RiskLevel.LOW
        add_case(db_session, school, index, level)
    add_case(db_session, school, 20, RiskLevel.HIGH, StudentStatus.TRANSFERRED)
    db_session.commit()
    return school


def test_metrics_compare_alerts_with_real_dropouts(
    client: TestClient, outcomes: School, today: list[date]
) -> None:
    body = client.get(URL, headers=auth(outcomes.analyst)).json()

    assert (body["labeled"], body["dropouts"], body["pending"]) == (20, 4, 0)
    assert body["model_versions"] == ["rf-test"]
    assert body["metrics"] == {
        "true_positives": 3,
        "false_negatives": 1,
        "false_positives": 2,
        "true_negatives": 14,
        "recall": 0.75,
        "precision": 0.6,
    }
    assert [case["alerted"] for case in body["cases"]] == [True, True, True, False]
    assert all(case["exit_reason"] == "WORK" for case in body["cases"])


def test_metrics_wait_until_enough_outcomes_are_known(
    client: TestClient, outcomes: School, today: list[date]
) -> None:
    today[0] = BEFORE_WINDOW

    body = client.get(URL, headers=auth(outcomes.director)).json()

    assert (body["labeled"], body["dropouts"], body["pending"]) == (4, 4, 16)
    assert body["metrics"] is None
    assert len(body["cases"]) == 4


def test_only_leadership_sees_model_performance(
    client: TestClient, outcomes: School, today: list[date]
) -> None:
    assert client.get(URL, headers=auth(outcomes.teacher)).status_code == 403
    assert client.get(f"{URL}/dataset.csv", headers=auth(outcomes.director)).status_code == 403


def test_dataset_is_anonymized(
    client: TestClient, evaluated_school: School, db_session: Session, today: list[date]
) -> None:
    school = evaluated_school
    school.student_a.status = StudentStatus.WITHDRAWN
    school.student_a.exit_date = date(2026, 6, 1)
    school.student_a.exit_reason = ExitReason.ECONOMIC
    db_session.add(
        RiskAssessment(
            student_id=school.student_a.id,
            period_id=school.period.id,
            probability=0.9,
            level=RiskLevel.HIGH,
            model_version="rf-test",
            top_factors=[],
        )
    )
    db_session.commit()

    response = client.get(f"{URL}/dataset.csv", headers=auth(school.analyst))

    lines = response.text.strip().splitlines()
    assert response.headers["content-type"].startswith("text/csv")
    assert lines[0].startswith("avg_score,") and lines[0].endswith(",dropout")
    assert len(lines) == 2 and lines[1].endswith(",1")
    assert "Flores" not in response.text and "A001" not in response.text
