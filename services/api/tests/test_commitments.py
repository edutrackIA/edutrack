from fastapi.testclient import TestClient

from tests.conftest import School, auth


def url(student_id: int, suffix: str = "") -> str:
    return f"/api/v1/students/{student_id}/commitments{suffix}"


def payload(school: School, **overrides: object) -> dict:
    data = {
        "guardian_id": school.parent.id,
        "meeting_date": "2026-06-12",
        "agreements": "Supervisar una hora diaria de estudio.",
        "follow_up_date": "2026-07-10",
    }
    return {**data, **overrides}


def create(client: TestClient, school: School) -> dict:
    response = client.post(
        url(school.student_a.id), json=payload(school), headers=auth(school.teacher)
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_tutor_registers_commitment(client: TestClient, school: School) -> None:
    body = create(client, school)

    assert body["tutor_id"] == school.teacher.id
    assert body["status"] == "OPEN"


def test_non_tutor_teacher_cannot_register_commitment(client: TestClient, school: School) -> None:
    response = client.post(
        url(school.student_a.id), json=payload(school), headers=auth(school.other_teacher)
    )

    assert response.status_code == 403


def test_guardian_must_belong_to_student(client: TestClient, school: School) -> None:
    response = client.post(
        url(school.student_a.id),
        json=payload(school, guardian_id=school.director.id),
        headers=auth(school.teacher),
    )

    assert response.status_code == 422


def test_follow_up_cannot_precede_meeting(client: TestClient, school: School) -> None:
    response = client.post(
        url(school.student_a.id),
        json=payload(school, follow_up_date="2026-06-01"),
        headers=auth(school.teacher),
    )

    assert response.status_code == 422


def test_parties_and_director_can_view_commitments(client: TestClient, school: School) -> None:
    create(client, school)

    for user in (school.teacher, school.parent, school.director):
        response = client.get(url(school.student_a.id), headers=auth(user))
        assert response.status_code == 200
        assert len(response.json()) == 1

    for user in (school.analyst, school.other_teacher):
        assert client.get(url(school.student_a.id), headers=auth(user)).status_code == 403


def test_tutor_updates_commitment_status(client: TestClient, school: School) -> None:
    commitment = create(client, school)

    response = client.patch(
        url(school.student_a.id, f"/{commitment['id']}"),
        json={"status": "FULFILLED"},
        headers=auth(school.teacher),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "FULFILLED"
    assert response.json()["agreements"] == commitment["agreements"]


def test_update_validates_follow_up_date(client: TestClient, school: School) -> None:
    commitment = create(client, school)

    response = client.patch(
        url(school.student_a.id, f"/{commitment['id']}"),
        json={"follow_up_date": "2026-01-01"},
        headers=auth(school.teacher),
    )

    assert response.status_code == 422


def test_parent_cannot_update_commitment(client: TestClient, school: School) -> None:
    commitment = create(client, school)

    response = client.patch(
        url(school.student_a.id, f"/{commitment['id']}"),
        json={"status": "BREACHED"},
        headers=auth(school.parent),
    )

    assert response.status_code == 403


def test_commitment_must_belong_to_student(client: TestClient, school: School) -> None:
    commitment = create(client, school)

    wrong_student = client.patch(
        url(school.student_a2.id, f"/{commitment['id']}"),
        json={"status": "FULFILLED"},
        headers=auth(school.teacher),
    )
    unknown = client.patch(
        url(school.student_a.id, "/9999"),
        json={"status": "FULFILLED"},
        headers=auth(school.teacher),
    )

    assert wrong_student.status_code == 404
    assert unknown.status_code == 404


def test_unknown_student_is_not_found(client: TestClient, school: School) -> None:
    assert client.get(url(9999), headers=auth(school.director)).status_code == 404
