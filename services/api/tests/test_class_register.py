from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_school_today
from app.main import app
from tests.conftest import School, auth

FRIDAY = date(2026, 3, 20)


@pytest.fixture(autouse=True)
def today() -> Iterator[None]:
    app.dependency_overrides[get_school_today] = lambda: FRIDAY
    yield
    app.dependency_overrides.pop(get_school_today, None)


# --- Lo que dicta el docente --------------------------------------------------------------


def test_teacher_sees_their_courses_and_classrooms(client: TestClient, school: School) -> None:
    body = client.get("/api/v1/me/teaching", headers=auth(school.teacher)).json()

    assert [(c["classroom"], c["subject"]) for c in body["courses"]] == [
        ("3° A", "Matemática"),
        ("3° B", "Comunicación"),
    ]
    assert [(c["classroom"], c["is_tutor"]) for c in body["classrooms"]] == [
        ("3° A", True),
        ("3° B", False),
    ]


# --- Notas -------------------------------------------------------------------------------


def gradebook_url(school: School) -> str:
    return (
        f"/api/v1/gradebook?classroom_id={school.classroom_a.id}"
        f"&subject_id={school.math.id}&period_id={school.period.id}"
    )


def save_grades(client: TestClient, school: School, scores: list[dict], user=None):
    return client.put(
        "/api/v1/gradebook",
        json={
            "classroom_id": school.classroom_a.id,
            "subject_id": school.math.id,
            "period_id": school.period.id,
            "scores": scores,
        },
        headers=auth(user or school.teacher),
    )


def test_teacher_records_and_corrects_course_grades(client: TestClient, school: School) -> None:
    empty = client.get(gradebook_url(school), headers=auth(school.teacher)).json()
    saved = save_grades(
        client,
        school,
        [
            {"student_id": school.student_a.id, "score": 14.5},
            {"student_id": school.student_a2.id, "score": 9},
        ],
    ).json()
    corrected = save_grades(client, school, [{"student_id": school.student_a2.id, "score": None}])

    assert [row["full_name"] for row in empty["rows"]] == ["Castillo, Mateo", "Flores, Lucía"]
    assert [row["score"] for row in empty["rows"]] == [None, None]
    assert [row["score"] for row in saved["rows"]] == [9.0, 14.5]
    assert [row["score"] for row in corrected.json()["rows"]] == [None, 14.5]


def test_only_the_course_teacher_or_staff_record_grades(client: TestClient, school: School) -> None:
    row = [{"student_id": school.student_a.id, "score": 15}]

    other = save_grades(client, school, row, school.other_teacher)
    analyst = save_grades(client, school, row, school.analyst)
    foreign = save_grades(client, school, [{"student_id": school.student_b.id, "score": 15}])
    out_of_range = save_grades(client, school, [{"student_id": school.student_a.id, "score": 21}])

    assert other.status_code == 403
    assert analyst.status_code == 200
    assert foreign.status_code == 422
    assert foreign.json()["code"] == "REGISTER_INVALID"
    assert out_of_range.status_code == 422


# --- Asistencia ---------------------------------------------------------------------------


def attendance_url(school: School, classroom=None) -> str:
    return f"/api/v1/classrooms/{(classroom or school.classroom_a).id}/attendance"


def mark(client: TestClient, school: School, day: str, user=None):
    return client.put(
        attendance_url(school),
        json={
            "date": day,
            "records": [
                {"student_id": school.student_a.id, "status": "ABSENT"},
                {"student_id": school.student_a2.id, "status": "PRESENT"},
            ],
        },
        headers=auth(user or school.teacher),
    )


def test_attendance_is_taken_for_a_school_day(client: TestClient, school: School) -> None:
    before = client.get(attendance_url(school), headers=auth(school.teacher)).json()
    saved = mark(client, school, "2026-03-20").json()

    assert before["date"] == "2026-03-20"
    assert before["period_id"] == school.period.id
    assert [row["status"] for row in before["rows"]] == [None, None]
    assert [row["status"] for row in saved["rows"]] == ["PRESENT", "ABSENT"]


@pytest.mark.parametrize(
    ("day", "message"),
    [
        ("2026-03-23", "días futuros"),
        ("2026-03-14", "de lunes a viernes"),
        ("2026-03-02", "ningún bimestre"),
    ],
)
def test_attendance_dates_are_validated(
    client: TestClient, school: School, day: str, message: str
) -> None:
    response = mark(client, school, day)

    assert response.status_code == 422
    assert message in response.json()["message"]


def test_teachers_without_courses_in_the_classroom_cannot_take_attendance(
    client: TestClient, school: School
) -> None:
    assert mark(client, school, "2026-03-20", school.other_teacher).status_code == 403
    assert mark(client, school, "2026-03-20", school.director).status_code == 200


# --- Conducta ----------------------------------------------------------------------------


def behavior_url(school: School) -> str:
    return f"/api/v1/classrooms/{school.classroom_a.id}/behavior"


def test_tutor_grades_conduct_once_per_period(client: TestClient, school: School) -> None:
    saved = client.put(
        behavior_url(school),
        json={
            "period_id": school.period.id,
            "ratings": [
                {"student_id": school.student_a.id, "rating": 4, "notes": "  Participa  "},
                {"student_id": school.student_a2.id, "rating": 2},
            ],
        },
        headers=auth(school.teacher),
    ).json()
    cleared = client.put(
        behavior_url(school),
        json={"period_id": school.period.id, "ratings": [{"student_id": school.student_a2.id}]},
        headers=auth(school.teacher),
    ).json()

    assert [(row["rating"], row["notes"]) for row in saved["rows"]] == [(2, None), (4, "Participa")]
    assert [row["rating"] for row in cleared["rows"]] == [None, 4]


def test_only_the_tutor_grades_conduct(client: TestClient, school: School) -> None:
    response = client.get(
        f"{behavior_url(school)}?period_id={school.period.id}", headers=auth(school.other_teacher)
    )
    invalid = client.put(
        behavior_url(school),
        json={
            "period_id": school.period.id,
            "ratings": [{"student_id": school.student_a.id, "rating": 6}],
        },
        headers=auth(school.teacher),
    )

    assert response.status_code == 403
    assert invalid.status_code == 422
