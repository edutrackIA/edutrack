from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import RiskAssessment, RiskLevel
from app.services.recommendations.catalog import ML_DISCLAIMER
from app.services.recommendations.generator import RecommendationGenerator
from tests.conftest import School, auth

QUEUE_URL = "/api/v1/recommendations"


def queue(client: TestClient, user, status: str = "PENDING_REVIEW") -> list[dict]:
    response = client.get(f"{QUEUE_URL}?status={status}", headers=auth(user))
    assert response.status_code == 200, response.text
    return response.json()


def recommendation_for(client: TestClient, school: School, student_id: int) -> dict:
    items = queue(client, school.teacher)
    return next(item for item in items if item["student"]["id"] == student_id)


# --- Generación ------------------------------------------------------------


def test_assessment_creates_pending_recommendations(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school

    items = queue(client, school.teacher)

    assert {item["student"]["id"] for item in items} == {
        school.student_a.id,
        school.student_a2.id,
    }
    high = recommendation_for(client, school, school.student_a.id)
    assert high["student"]["risk_level"] == "HIGH"
    assert high["parent_items"][0].startswith("Rendimiento:")
    assert "Teacher" in high["parent_items"][-1]
    low = recommendation_for(client, school, school.student_a2.id)
    assert low["parent_items"][0].startswith("Buen desempeño: Mateo")


def test_family_messages_never_mention_risk(client: TestClient, assessed_school: School) -> None:
    for item in queue(client, assessed_school.teacher):
        text = " ".join(item["parent_items"]).lower()
        assert "riesgo" not in text
        assert "probabilidad" not in text


def test_generator_names_failing_subjects(evaluated_school: School, db_session: Session) -> None:
    school = evaluated_school
    assessment = RiskAssessment(
        student_id=school.student_a.id,
        period_id=school.period.id,
        probability=0.8,
        level=RiskLevel.HIGH,
        model_version="rf-test",
        top_factors=[
            {"feature": "failed_subjects", "value": 2, "contribution": 0.3},
            {"feature": "attendance_rate", "value": 0.7, "contribution": 0.2},
            {"feature": "parent_education", "value": "SECONDARY", "contribution": 0.1},
        ],
    )

    result = RecommendationGenerator(db_session).generate(school.student_a, assessment)

    assert result.parent_items[0] == (
        "Cursos a reforzar: Comunicación, Matemática. Acordar un horario fijo de estudio en "
        "casa, de al menos una hora diaria, puede ayudarle mucho."
    )
    assert result.parent_items[1].startswith("Asistencia: Lucía")
    assert len(result.parent_items) == 3
    assert result.teacher_items[0] == "Derivar a reforzamiento en: Comunicación, Matemática."


def test_tutor_receives_alert_only_for_moderate_or_high_risk(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school

    teacher = client.get("/api/v1/alerts?unread=true", headers=auth(school.teacher)).json()
    other = client.get("/api/v1/alerts", headers=auth(school.other_teacher)).json()

    assert teacher["total"] == 1
    assert teacher["items"][0]["student"]["id"] == school.student_a.id
    assert teacher["items"][0]["level"] == "HIGH"
    assert other["total"] == 0


def test_rerun_does_not_duplicate_alerts_or_recommendations(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school
    client.post(
        "/api/v1/risk-assessments/run",
        json={"period_id": school.period.id},
        headers=auth(school.analyst),
    )

    assert len(queue(client, school.teacher)) == 2
    assert client.get("/api/v1/alerts", headers=auth(school.teacher)).json()["total"] == 1


def test_rerun_keeps_reviewed_recommendations(
    client: TestClient, assessed_school: School, db_session: Session
) -> None:
    school = assessed_school
    item = recommendation_for(client, school, school.student_a.id)
    client.patch(
        f"{QUEUE_URL}/{item['id']}",
        json={"parent_items": ["Mensaje editado por el tutor."]},
        headers=auth(school.teacher),
    )
    client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))

    client.post(
        "/api/v1/risk-assessments/run",
        json={"period_id": school.period.id},
        headers=auth(school.analyst),
    )

    approved = queue(client, school.teacher, "APPROVED")
    assert approved[0]["parent_items"] == ["Mensaje editado por el tutor."]


# --- Revisión --------------------------------------------------------------


def test_tutor_edits_and_approves(client: TestClient, assessed_school: School) -> None:
    school = assessed_school
    item = recommendation_for(client, school, school.student_a.id)

    edited = client.patch(
        f"{QUEUE_URL}/{item['id']}",
        json={"parent_items": ["Revisen juntos las tareas cada noche."]},
        headers=auth(school.teacher),
    )
    approved = client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))
    again = client.post(f"{QUEUE_URL}/{item['id']}/discard", headers=auth(school.teacher))

    assert edited.json()["parent_items"] == ["Revisen juntos las tareas cada noche."]
    assert approved.json()["status"] == "APPROVED"
    assert approved.json()["reviewed_by"] == school.teacher.id
    assert again.status_code == 409


def test_tutor_can_discard(client: TestClient, assessed_school: School) -> None:
    school = assessed_school
    item = recommendation_for(client, school, school.student_a2.id)

    response = client.post(f"{QUEUE_URL}/{item['id']}/discard", headers=auth(school.teacher))

    assert response.json()["status"] == "DISCARDED"


def test_only_the_tutor_or_director_can_review(client: TestClient, assessed_school: School) -> None:
    school = assessed_school
    item = recommendation_for(client, school, school.student_a.id)

    other_teacher = client.post(
        f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.other_teacher)
    )
    parent = client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.parent))
    director = client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.director))
    missing = client.post(f"{QUEUE_URL}/9999/approve", headers=auth(school.director))

    assert other_teacher.status_code == 403
    assert parent.status_code == 403
    assert director.status_code == 200
    assert missing.status_code == 404


def test_review_queue_is_scoped(client: TestClient, assessed_school: School) -> None:
    school = assessed_school

    assert queue(client, school.other_teacher) == []
    assert len(queue(client, school.director)) == 2
    assert len(queue(client, school.director, "APPROVED")) == 0


def test_edit_requires_at_least_one_item(client: TestClient, assessed_school: School) -> None:
    school = assessed_school
    item = recommendation_for(client, school, school.student_a.id)

    response = client.patch(
        f"{QUEUE_URL}/{item['id']}", json={"parent_items": []}, headers=auth(school.teacher)
    )

    assert response.status_code == 422


# --- Familias --------------------------------------------------------------


def test_parent_sees_only_approved_recommendations(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school
    url = f"/api/v1/students/{school.student_a.id}/summary"

    before = client.get(url, headers=auth(school.parent)).json()
    item = recommendation_for(client, school, school.student_a.id)
    client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))
    after = client.get(url, headers=auth(school.parent)).json()

    assert before["parent_suggestions"] == []
    assert before["disclaimer"] is None
    assert after["parent_suggestions"] == item["parent_items"]
    assert after["disclaimer"] == ML_DISCLAIMER


def test_student_recommendations_are_staff_only(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school
    url = f"/api/v1/students/{school.student_a.id}/recommendations"

    assert len(client.get(url, headers=auth(school.director)).json()) == 1
    assert client.get(url, headers=auth(school.parent)).status_code == 403
    assert (
        client.get(
            "/api/v1/students/9999/recommendations", headers=auth(school.director)
        ).status_code
        == 404
    )


# --- Alertas ---------------------------------------------------------------


def test_mark_alert_as_read(
    client: TestClient, assessed_school: School, db_session: Session
) -> None:
    school = assessed_school
    alert = client.get("/api/v1/alerts", headers=auth(school.teacher)).json()["items"][0]

    updated = client.patch(
        f"/api/v1/alerts/{alert['id']}", json={"is_read": True}, headers=auth(school.teacher)
    )
    unread = client.get("/api/v1/alerts?unread=true", headers=auth(school.teacher)).json()
    foreign = client.patch(
        f"/api/v1/alerts/{alert['id']}", json={"is_read": False}, headers=auth(school.director)
    )

    assert updated.json()["is_read"] is True
    assert unread["total"] == 0
    assert foreign.status_code == 404
    assert db_session.scalar(select(RiskAssessment.id)) is not None
