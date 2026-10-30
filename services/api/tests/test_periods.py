from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain import Grade
from tests.conftest import School, auth


def test_periods_of_the_institution_are_listed(client: TestClient, school: School) -> None:
    response = client.get("/api/v1/periods", headers=auth(school.teacher))

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": school.period.id,
            "year": 2026,
            "bimester": 1,
            "start_date": "2026-03-09",
            "end_date": "2026-05-08",
            "label": "Bimestre 1, 2026",
            "has_grades": False,
        }
    ]


def test_periods_report_whether_they_have_grades(
    client: TestClient, school: School, db_session: Session
) -> None:
    db_session.add(
        Grade(
            student_id=school.student_a.id,
            subject_id=school.math.id,
            period_id=school.period.id,
            score=14,
        )
    )
    db_session.commit()

    body = client.get("/api/v1/periods", headers=auth(school.teacher)).json()

    assert body[0]["has_grades"] is True


def test_periods_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/periods").status_code == 401
