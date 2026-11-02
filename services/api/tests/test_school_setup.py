from fastapi.testclient import TestClient

from tests.conftest import Outbox, School, auth


def post(client: TestClient, school: School, url: str, body: dict, user=None):  # noqa: ANN001
    return client.post(f"/api/v1{url}", json=body, headers=auth(user or school.director))


# --- Bimestres -----------------------------------------------------------------------


def test_director_creates_a_period(client: TestClient, school: School) -> None:
    body = {"year": 2026, "bimester": 2, "start_date": "2026-05-18", "end_date": "2026-07-17"}

    created = post(client, school, "/periods", body)
    duplicated = post(client, school, "/periods", body)
    teacher = post(client, school, "/periods", body, school.teacher)

    assert created.status_code == 201
    assert created.json()["label"] == "Bimestre 2, 2026"
    assert created.json()["has_grades"] is False
    assert duplicated.status_code == 409
    assert teacher.status_code == 403


def test_period_dates_are_validated(client: TestClient, school: School) -> None:
    overlap = post(
        client,
        school,
        "/periods",
        {"year": 2026, "bimester": 2, "start_date": "2026-05-01", "end_date": "2026-07-17"},
    )
    reversed_dates = post(
        client,
        school,
        "/periods",
        {"year": 2026, "bimester": 3, "start_date": "2026-09-30", "end_date": "2026-08-01"},
    )
    other_year = post(
        client,
        school,
        "/periods",
        {"year": 2026, "bimester": 4, "start_date": "2026-12-01", "end_date": "2027-01-15"},
    )

    assert overlap.status_code == 422
    assert "se cruzan con el bimestre 1" in overlap.json()["message"]
    assert reversed_dates.json()["code"] == "SETUP_INVALID"
    assert "dentro del año 2026" in other_year.json()["message"]


def test_period_dates_can_be_corrected(client: TestClient, school: School) -> None:
    response = client.patch(
        f"/api/v1/periods/{school.period.id}",
        json={"start_date": "2026-03-16", "end_date": "2026-05-15"},
        headers=auth(school.director),
    )

    assert response.status_code == 200
    assert response.json()["start_date"] == "2026-03-16"


# --- Cursos -------------------------------------------------------------------------


def test_courses_are_managed_per_school(client: TestClient, school: School) -> None:
    created = post(client, school, "/subjects", {"name": "  Arte   y Cultura "})
    duplicated = post(client, school, "/subjects", {"name": "matemática"})
    renamed = client.patch(
        f"/api/v1/subjects/{created.json()['id']}",
        json={"name": "Arte"},
        headers=auth(school.director),
    )
    listed = client.get("/api/v1/subjects", headers=auth(school.teacher)).json()

    assert created.json()["name"] == "Arte y Cultura"
    assert duplicated.status_code == 409
    assert duplicated.json()["message"] == "Ya existe el curso Matemática"
    assert renamed.json()["name"] == "Arte"
    assert [item["name"] for item in listed] == ["Arte", "Comunicación", "Matemática"]


# --- Aulas --------------------------------------------------------------------------


def test_director_creates_classrooms_and_assigns_tutors(client: TestClient, school: School) -> None:
    created = post(client, school, "/classrooms", {"year": 2026, "grade": 4, "section": "c"})
    duplicated = post(client, school, "/classrooms", {"year": 2026, "grade": 4, "section": "C"})
    tutor = client.patch(
        f"/api/v1/classrooms/{created.json()['id']}",
        json={"tutor_id": school.other_teacher.id},
        headers=auth(school.director),
    )
    not_a_teacher = client.patch(
        f"/api/v1/classrooms/{created.json()['id']}",
        json={"tutor_id": school.analyst.id},
        headers=auth(school.director),
    )

    assert created.status_code == 201
    assert created.json()["section"] == "C"
    assert duplicated.status_code == 409
    assert tutor.json()["tutor"]["id"] == school.other_teacher.id
    assert not_a_teacher.status_code == 422


# --- Personal -------------------------------------------------------------------------


def test_director_invites_staff(client: TestClient, school: School, outbox: Outbox) -> None:
    invited = post(
        client,
        school,
        "/staff",
        {"full_name": "Ana Torres", "email": "Ana.Torres@colegio.edu.pe", "role": "TEACHER"},
    )
    duplicated = post(
        client,
        school,
        "/staff",
        {"full_name": "Otra", "email": "teacher@school.dev", "role": "ANALYST"},
    )
    staff = client.get("/api/v1/staff", headers=auth(school.director)).json()

    assert invited.status_code == 201
    assert invited.json()["has_access"] is False
    assert invited.json()["invitation_sent"] is True
    assert outbox.messages[0]["To"] == "ana.torres@colegio.edu.pe"
    assert "registró como docente" in outbox.messages[0].get_body(("plain",)).get_content()
    assert duplicated.status_code == 409
    assert "parent@school.dev" not in [member["email"] for member in staff]


def test_deactivated_staff_cannot_log_in(client: TestClient, school: School) -> None:
    deactivated = client.patch(
        f"/api/v1/staff/{school.teacher.id}",
        json={"is_active": False},
        headers=auth(school.director),
    )
    self_deactivation = client.patch(
        f"/api/v1/staff/{school.director.id}",
        json={"is_active": False},
        headers=auth(school.director),
    )
    parent = client.patch(
        f"/api/v1/staff/{school.parent.id}",
        json={"is_active": False},
        headers=auth(school.director),
    )

    assert deactivated.json()["is_active"] is False
    assert client.get("/api/v1/auth/me", headers=auth(school.teacher)).status_code == 401
    assert self_deactivation.status_code == 422
    assert parent.status_code == 404


# --- Asignaciones ---------------------------------------------------------------------


def test_course_assignments(client: TestClient, school: School) -> None:
    body = {
        "classroom_id": school.classroom_b.id,
        "subject_id": school.math.id,
        "teacher_id": school.other_teacher.id,
    }

    created = post(client, school, "/course-assignments", body)
    duplicated = post(client, school, "/course-assignments", body)
    language_taken = post(
        client, school, "/course-assignments", body | {"subject_id": school.language.id}
    )
    listed = client.get(
        f"/api/v1/course-assignments?classroom_id={school.classroom_b.id}",
        headers=auth(school.director),
    ).json()
    removed = client.delete(
        f"/api/v1/course-assignments/{created.json()['id']}", headers=auth(school.director)
    )

    assert created.status_code == 201
    assert created.json()["subject"] == "Matemática"
    assert duplicated.status_code == 409
    assert language_taken.status_code == 409
    assert {item["subject"] for item in listed} == {"Matemática", "Comunicación"}
    assert removed.status_code == 204
