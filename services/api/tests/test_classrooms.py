from fastapi.testclient import TestClient

from tests.conftest import School, auth


def test_director_sees_every_classroom_of_the_institution(
    client: TestClient, school: School
) -> None:
    response = client.get("/api/v1/classrooms", headers=auth(school.director))

    assert response.status_code == 200
    body = response.json()
    assert [(c["grade"], c["section"]) for c in body] == [(3, "A"), (3, "B")]
    assert body[0]["student_count"] == 2
    assert body[0]["tutor"]["email"] == "teacher@school.dev"


def test_teacher_sees_tutored_and_assigned_classrooms_only(
    client: TestClient, school: School
) -> None:
    response = client.get("/api/v1/classrooms", headers=auth(school.other_teacher))

    assert response.status_code == 200
    assert [c["section"] for c in response.json()] == ["B"]


def test_classrooms_can_be_filtered_by_year(client: TestClient, school: School) -> None:
    response = client.get("/api/v1/classrooms?year=2025", headers=auth(school.director))

    assert response.json() == []


def test_parent_cannot_list_classrooms(client: TestClient, school: School) -> None:
    response = client.get("/api/v1/classrooms", headers=auth(school.parent))

    assert response.status_code == 403


def test_list_classroom_students_sorted_by_last_name(client: TestClient, school: School) -> None:
    url = f"/api/v1/classrooms/{school.classroom_a.id}/students"

    response = client.get(url, headers=auth(school.teacher))

    assert response.status_code == 200
    assert [s["full_name"] for s in response.json()] == ["Castillo, Mateo", "Flores, Lucía"]
    assert response.json()[0]["classroom"] == "3° A"


def test_teacher_cannot_list_students_of_unrelated_classroom(
    client: TestClient, school: School
) -> None:
    url = f"/api/v1/classrooms/{school.classroom_a.id}/students"

    response = client.get(url, headers=auth(school.other_teacher))

    assert response.status_code == 403


def test_classroom_from_another_institution_is_not_found(
    client: TestClient, school: School
) -> None:
    url = f"/api/v1/classrooms/{school.foreign_classroom.id}/students"

    response = client.get(url, headers=auth(school.director))

    assert response.status_code == 404


def test_unknown_classroom_is_not_found(client: TestClient, school: School) -> None:
    response = client.get("/api/v1/classrooms/9999/students", headers=auth(school.director))

    assert response.status_code == 404
