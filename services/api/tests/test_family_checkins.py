from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_school_today
from app.main import app
from tests.conftest import Outbox, School, auth


@pytest.fixture(autouse=True)
def today() -> Iterator[None]:
    app.dependency_overrides[get_school_today] = lambda: date(2026, 10, 28)
    yield
    app.dependency_overrides.pop(get_school_today, None)


def url(student_id: int) -> str:
    return f"/api/v1/students/{student_id}/family-checkins/current"


def submit(client: TestClient, school: School, **overrides: object):
    payload = {"mood": "OK", "home_changes": [], "peer_concern": False} | overrides
    return client.put(url(school.student_a.id), json=payload, headers=auth(school.parent))


def test_family_submits_and_edits_this_month(client: TestClient, school: School) -> None:
    empty = client.get(url(school.student_a.id), headers=auth(school.parent)).json()
    first = submit(client, school, home_changes=["MOVING", "MOVING"], comment="  Nos mudamos.  ")
    edited = submit(client, school, mood="GOOD")
    current = client.get(url(school.student_a.id), headers=auth(school.parent)).json()

    assert empty == {"month": "2026-10-01", "checkin": None}
    assert first.status_code == 200
    assert first.json()["home_change_labels"] == ["Mudanza"]
    assert first.json()["comment"] == "Nos mudamos."
    assert edited.json()["id"] == first.json()["id"]
    assert current["checkin"]["mood_label"] == "Lo vemos bien"


def test_only_the_childs_guardian_answers(client: TestClient, school: School) -> None:
    payload = {"mood": "OK"}

    other_child = client.put(url(school.student_a2.id), json=payload, headers=auth(school.parent))
    teacher = client.put(url(school.student_a.id), json=payload, headers=auth(school.teacher))

    assert other_child.status_code == 403
    assert teacher.status_code == 403


def test_peer_concern_alerts_the_tutor_right_away(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    submit(client, school, peer_concern=True)
    submit(client, school, peer_concern=True, comment="Sigue igual.")

    assert [message["To"] for message in outbox.messages] == ["teacher@school.dev"]
    assert outbox.messages[0]["Subject"].startswith("Prioritario:")


def test_tutor_reviews_reports_that_need_attention(client: TestClient, school: School) -> None:
    submit(client, school, mood="WORRIED", home_changes=["HEALTH"])

    tutor = client.get("/api/v1/family-checkins/pending", headers=auth(school.teacher)).json()
    other = client.get("/api/v1/family-checkins/pending", headers=auth(school.other_teacher)).json()
    reviewed = client.post(
        f"/api/v1/family-checkins/{tutor[0]['id']}/review", headers=auth(school.teacher)
    )
    again = client.post(
        f"/api/v1/family-checkins/{tutor[0]['id']}/review", headers=auth(school.teacher)
    )
    after = client.get("/api/v1/family-checkins/pending", headers=auth(school.teacher)).json()

    assert [item["student"]["code"] for item in tutor] == ["A001"]
    assert other == []
    assert reviewed.json()["reviewed_at"] is not None
    assert again.status_code == 409
    assert after == []


def test_calm_reports_do_not_need_review(client: TestClient, school: School) -> None:
    submit(client, school, mood="GOOD")

    pending = client.get("/api/v1/family-checkins/pending", headers=auth(school.director)).json()

    assert pending == []


def test_editing_sends_the_report_back_to_the_tutor(client: TestClient, school: School) -> None:
    first = submit(client, school, mood="WORRIED").json()
    client.post(f"/api/v1/family-checkins/{first['id']}/review", headers=auth(school.teacher))

    submit(client, school, mood="WORRIED", comment="Ahora también le cuesta dormir.")

    pending = client.get("/api/v1/family-checkins/pending", headers=auth(school.teacher)).json()
    assert len(pending) == 1


def test_unknown_check_in_is_not_found(client: TestClient, school: School) -> None:
    response = client.post("/api/v1/family-checkins/9999/review", headers=auth(school.teacher))

    assert response.status_code == 404
