from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain import Attendance, AttendanceStatus, Grade
from tests.conftest import School, auth


def survey_payload(school: School, **overrides: object) -> dict:
    payload = {
        "period_id": school.period.id,
        "study_hours_week": 8,
        "parent_education": "SECONDARY",
        "home_internet": True,
        "has_study_device": False,
        "family_communication": 4,
        "student_works": False,
        "household_size": 5,
    }
    return {**payload, **overrides}


def surveys_url(student_id: int) -> str:
    return f"/api/v1/students/{student_id}/surveys"


# --- Encuestas -------------------------------------------------------------


def test_parent_submits_survey_for_own_child(client: TestClient, school: School) -> None:
    response = client.post(
        surveys_url(school.student_a.id), json=survey_payload(school), headers=auth(school.parent)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["responder_id"] == school.parent.id
    assert body["parent_education"] == "SECONDARY"


def test_parent_cannot_submit_survey_for_other_student(client: TestClient, school: School) -> None:
    response = client.post(
        surveys_url(school.student_a2.id), json=survey_payload(school), headers=auth(school.parent)
    )

    assert response.status_code == 403


def test_analyst_can_submit_survey_on_behalf_of_family(client: TestClient, school: School) -> None:
    response = client.post(
        surveys_url(school.student_b.id), json=survey_payload(school), headers=auth(school.analyst)
    )

    assert response.status_code == 201


def test_teacher_cannot_submit_survey(client: TestClient, school: School) -> None:
    response = client.post(
        surveys_url(school.student_a.id), json=survey_payload(school), headers=auth(school.teacher)
    )

    assert response.status_code == 403


def test_only_one_survey_per_period(client: TestClient, school: School) -> None:
    url = surveys_url(school.student_a.id)
    client.post(url, json=survey_payload(school), headers=auth(school.parent))

    second = client.post(url, json=survey_payload(school), headers=auth(school.parent))

    assert second.status_code == 409
    assert second.json()["code"] == "CONFLICT"


def test_survey_validates_period_and_ranges(client: TestClient, school: School) -> None:
    url = surveys_url(school.student_a.id)

    foreign = client.post(
        url,
        json=survey_payload(school, period_id=school.foreign_period.id),
        headers=auth(school.parent),
    )
    out_of_range = client.post(
        url, json=survey_payload(school, family_communication=9), headers=auth(school.parent)
    )

    assert foreign.status_code == 422
    assert out_of_range.status_code == 422


def test_survey_visibility_excludes_teachers(client: TestClient, school: School) -> None:
    url = surveys_url(school.student_a.id)
    client.post(url, json=survey_payload(school), headers=auth(school.parent))

    director = client.get(url, headers=auth(school.director))
    parent = client.get(url, headers=auth(school.parent))
    teacher = client.get(url, headers=auth(school.teacher))

    assert len(director.json()) == 1
    assert len(parent.json()) == 1
    assert teacher.status_code == 403


def test_surveys_of_unknown_student_are_not_found(client: TestClient, school: School) -> None:
    response = client.get(surveys_url(9999), headers=auth(school.director))

    assert response.status_code == 404


# --- Resumen ---------------------------------------------------------------


def test_summary_uses_latest_period_with_grades(
    client: TestClient, school: School, db_session: Session
) -> None:
    student = school.student_a
    db_session.add_all(
        [
            Grade(
                student_id=student.id,
                subject_id=school.math.id,
                period_id=school.period.id,
                score=14,
            ),
            Grade(
                student_id=student.id,
                subject_id=school.language.id,
                period_id=school.period.id,
                score=17,
            ),
        ]
    )
    start = school.period.start_date
    statuses = [AttendanceStatus.PRESENT] * 6 + [AttendanceStatus.ABSENT, AttendanceStatus.LATE]
    db_session.add_all(
        Attendance(student_id=student.id, date=start + timedelta(days=i), status=s)
        for i, s in enumerate(statuses)
    )
    db_session.add(
        Attendance(student_id=student.id, date=date(2026, 12, 1), status=AttendanceStatus.ABSENT)
    )
    db_session.commit()

    response = client.get(f"/api/v1/students/{student.id}/summary", headers=auth(school.parent))

    assert response.status_code == 200
    body = response.json()
    assert body["period_id"] == school.period.id
    assert body["average_score"] == 15.5
    assert body["attendance_rate"] == 0.875
    assert [g["subject"] for g in body["grades"]] == ["Comunicación", "Matemática"]
    assert body["parent_suggestions"] == []


def test_summary_without_data_returns_empty_values(client: TestClient, school: School) -> None:
    response = client.get(
        f"/api/v1/students/{school.student_a2.id}/summary", headers=auth(school.director)
    )

    assert response.json()["period_id"] is None
    assert response.json()["average_score"] is None
    assert response.json()["attendance_rate"] is None


def test_summary_for_explicit_period_without_attendance(client: TestClient, school: School) -> None:
    url = f"/api/v1/students/{school.student_a2.id}/summary?period_id={school.period.id}"

    response = client.get(url, headers=auth(school.director))

    assert response.json()["period_id"] == school.period.id
    assert response.json()["attendance_rate"] is None


def test_parent_cannot_see_summary_of_other_student(client: TestClient, school: School) -> None:
    response = client.get(
        f"/api/v1/students/{school.student_a2.id}/summary", headers=auth(school.parent)
    )

    assert response.status_code == 403
