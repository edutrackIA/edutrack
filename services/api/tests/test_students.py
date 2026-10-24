from fastapi.testclient import TestClient

from tests.conftest import School, auth


def student_url(student_id: int, suffix: str = "") -> str:
    return f"/api/v1/students/{student_id}{suffix}"


# --- Ficha -----------------------------------------------------------------


def test_director_can_view_student_with_guardians(client: TestClient, school: School) -> None:
    response = client.get(student_url(school.student_a.id), headers=auth(school.director))

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "A001"
    assert body["guardians"][0]["email"] == "parent@school.dev"
    assert body["latest_risk"] is None


def test_parent_can_view_own_child_only(client: TestClient, school: School) -> None:
    own = client.get(student_url(school.student_a.id), headers=auth(school.parent))
    other = client.get(student_url(school.student_a2.id), headers=auth(school.parent))

    assert own.status_code == 200
    assert other.status_code == 403


def test_teacher_can_view_students_of_assigned_classroom(
    client: TestClient, school: School
) -> None:
    response = client.get(student_url(school.student_b.id), headers=auth(school.teacher))

    assert response.status_code == 200


def test_teacher_cannot_view_students_of_unrelated_classroom(
    client: TestClient, school: School
) -> None:
    response = client.get(student_url(school.student_a.id), headers=auth(school.other_teacher))

    assert response.status_code == 403


def test_student_from_another_institution_is_not_found(client: TestClient, school: School) -> None:
    response = client.get(student_url(school.foreign_student.id), headers=auth(school.director))

    assert response.status_code == 404


def test_unknown_student_is_not_found(client: TestClient, school: School) -> None:
    response = client.get(student_url(9999), headers=auth(school.director))

    assert response.status_code == 404


# --- Actualización ---------------------------------------------------------


def test_analyst_can_update_student(client: TestClient, school: School) -> None:
    response = client.patch(
        student_url(school.student_a.id),
        json={"first_name": "Lucía María", "classroom_id": school.classroom_b.id},
        headers=auth(school.analyst),
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Lucía María"
    assert response.json()["classroom_id"] == school.classroom_b.id


def test_teacher_cannot_update_student(client: TestClient, school: School) -> None:
    response = client.patch(
        student_url(school.student_a.id), json={"first_name": "X"}, headers=auth(school.teacher)
    )

    assert response.status_code == 403


def test_update_rejects_classroom_from_another_institution(
    client: TestClient, school: School
) -> None:
    response = client.patch(
        student_url(school.student_a.id),
        json={"classroom_id": school.foreign_classroom.id},
        headers=auth(school.analyst),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


# --- Notas -----------------------------------------------------------------


def grade(school: School, score: float, subject_id: int | None = None) -> dict:
    return {
        "subject_id": subject_id or school.math.id,
        "period_id": school.period.id,
        "score": score,
    }


def test_teacher_records_grades_for_assigned_subject(client: TestClient, school: School) -> None:
    url = student_url(school.student_a.id, "/grades")

    created = client.put(url, json=[grade(school, 14)], headers=auth(school.teacher))
    updated = client.put(url, json=[grade(school, 16.5)], headers=auth(school.teacher))
    listed = client.get(url, headers=auth(school.director))

    assert created.status_code == 200
    assert updated.json()[0]["score"] == 16.5
    assert listed.json() == [
        {
            "subject_id": school.math.id,
            "subject": "Matemática",
            "period_id": school.period.id,
            "score": 16.5,
        }
    ]


def test_grades_can_be_filtered_by_period(client: TestClient, school: School) -> None:
    url = student_url(school.student_a.id, "/grades")
    client.put(url, json=[grade(school, 12)], headers=auth(school.analyst))

    response = client.get(f"{url}?period_id=9999", headers=auth(school.director))

    assert response.json() == []


def test_teacher_cannot_grade_unassigned_subject(client: TestClient, school: School) -> None:
    response = client.put(
        student_url(school.student_a.id, "/grades"),
        json=[grade(school, 14, subject_id=school.language.id)],
        headers=auth(school.teacher),
    )

    assert response.status_code == 403


def test_grades_reject_invalid_subject_and_period(client: TestClient, school: School) -> None:
    url = student_url(school.student_a.id, "/grades")
    bad_period = {**grade(school, 14), "period_id": school.foreign_period.id}

    subject = client.put(url, json=[grade(school, 14, 9999)], headers=auth(school.analyst))
    period = client.put(url, json=[bad_period], headers=auth(school.analyst))

    assert subject.status_code == 422
    assert period.status_code == 422


def test_grades_reject_duplicates_and_out_of_range_scores(
    client: TestClient, school: School
) -> None:
    url = student_url(school.student_a.id, "/grades")

    duplicated = client.put(
        url, json=[grade(school, 10), grade(school, 11)], headers=auth(school.analyst)
    )
    out_of_range = client.put(url, json=[grade(school, 21)], headers=auth(school.analyst))
    empty = client.put(url, json=[], headers=auth(school.analyst))

    assert duplicated.status_code == 422
    assert out_of_range.status_code == 422
    assert empty.status_code == 422


# --- Conducta --------------------------------------------------------------


def test_tutor_records_and_updates_behavior(client: TestClient, school: School) -> None:
    url = student_url(school.student_a.id, "/behavior")
    payload = {"period_id": school.period.id, "rating": 4, "notes": "Participa en clase"}

    created = client.put(url, json=payload, headers=auth(school.teacher))
    updated = client.put(url, json={**payload, "rating": 2}, headers=auth(school.teacher))

    assert created.status_code == 200
    assert updated.json() == {
        "period_id": school.period.id,
        "rating": 2,
        "notes": "Participa en clase",
    }


def test_non_tutor_teacher_cannot_record_behavior(client: TestClient, school: School) -> None:
    response = client.put(
        student_url(school.student_b.id, "/behavior"),
        json={"period_id": school.period.id, "rating": 4},
        headers=auth(school.teacher),
    )

    assert response.status_code == 403


def test_behavior_rejects_period_from_another_institution(
    client: TestClient, school: School
) -> None:
    response = client.put(
        student_url(school.student_a.id, "/behavior"),
        json={"period_id": school.foreign_period.id, "rating": 4},
        headers=auth(school.analyst),
    )

    assert response.status_code == 422


# --- Portal de padres ------------------------------------------------------


def test_parent_lists_own_children(client: TestClient, school: School) -> None:
    response = client.get("/api/v1/me/children", headers=auth(school.parent))

    assert response.status_code == 200
    assert [s["code"] for s in response.json()] == ["A001"]


def test_only_parents_can_list_children(client: TestClient, school: School) -> None:
    response = client.get("/api/v1/me/children", headers=auth(school.director))

    assert response.status_code == 403
