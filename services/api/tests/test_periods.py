from fastapi.testclient import TestClient

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
        }
    ]


def test_periods_require_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/periods").status_code == 401
