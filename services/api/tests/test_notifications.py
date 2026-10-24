from email.message import EmailMessage

import pytest
from fastapi.testclient import TestClient

from app.services.notifications.email_sender import SmtpEmailSender
from app.services.recommendations.catalog import ML_DISCLAIMER
from tests.conftest import Outbox, School, auth

QUEUE_URL = "/api/v1/recommendations"


def pending_for(client: TestClient, school: School, student_id: int) -> dict:
    items = client.get(f"{QUEUE_URL}?status=PENDING_REVIEW", headers=auth(school.teacher)).json()
    return next(item for item in items if item["student"]["id"] == student_id)


def body_of(message: EmailMessage, subtype: str) -> str:
    part = message.get_body(preferencelist=(subtype,))
    assert part is not None
    return part.get_content()


def test_approval_emails_the_guardian(
    client: TestClient, assessed_school: School, outbox: Outbox
) -> None:
    school = assessed_school
    item = pending_for(client, school, school.student_a.id)

    response = client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))

    assert response.json()["sent_at"] is not None
    assert len(outbox.messages) == 1
    message = outbox.messages[0]
    assert message["To"] == "parent@school.dev"
    assert message["Subject"] == "Recomendaciones para Lucía — 1.° bimestre"
    text = body_of(message, "plain")
    assert text.startswith("Hola, Parent:")
    assert item["parent_items"][0] in text
    assert ML_DISCLAIMER in text
    html = body_of(message, "html")
    assert "Machine Learning" in html
    assert "riesgo" not in text.lower()


def test_students_without_guardians_are_not_emailed(
    client: TestClient, assessed_school: School, outbox: Outbox
) -> None:
    school = assessed_school
    item = pending_for(client, school, school.student_a2.id)

    response = client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))

    assert response.json()["status"] == "APPROVED"
    assert response.json()["sent_at"] is None
    assert outbox.messages == []


def test_email_failure_keeps_approval_and_allows_resend(
    client: TestClient, assessed_school: School, outbox: Outbox
) -> None:
    school = assessed_school
    item = pending_for(client, school, school.student_a.id)
    outbox.fail = True

    approved = client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))
    failed_resend = client.post(f"{QUEUE_URL}/{item['id']}/send", headers=auth(school.teacher))
    outbox.fail = False
    resend = client.post(f"{QUEUE_URL}/{item['id']}/send", headers=auth(school.teacher))

    assert approved.json()["status"] == "APPROVED"
    assert approved.json()["sent_at"] is None
    assert failed_resend.status_code == 502
    assert failed_resend.json()["code"] == "EMAIL_NOT_SENT"
    assert resend.json()["sent_at"] is not None
    assert len(outbox.messages) == 1


def test_only_approved_recommendations_can_be_sent(
    client: TestClient, assessed_school: School
) -> None:
    school = assessed_school
    item = pending_for(client, school, school.student_a.id)

    pending = client.post(f"{QUEUE_URL}/{item['id']}/send", headers=auth(school.teacher))
    other = client.post(f"{QUEUE_URL}/{item['id']}/send", headers=auth(school.other_teacher))
    missing = client.post(f"{QUEUE_URL}/9999/send", headers=auth(school.director))

    assert pending.status_code == 409
    assert other.status_code == 403
    assert missing.status_code == 404


def test_html_escapes_user_content(
    client: TestClient, assessed_school: School, outbox: Outbox
) -> None:
    school = assessed_school
    item = pending_for(client, school, school.student_a.id)
    client.patch(
        f"{QUEUE_URL}/{item['id']}",
        json={"parent_items": ["<script>alert(1)</script> Revisen las tareas."]},
        headers=auth(school.teacher),
    )

    client.post(f"{QUEUE_URL}/{item['id']}/approve", headers=auth(school.teacher))

    html = body_of(outbox.messages[0], "html")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


class FakeSmtp:
    instances: list["FakeSmtp"] = []

    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host, self.port = host, port
        self.calls: list[str] = []
        FakeSmtp.instances.append(self)

    def __enter__(self) -> "FakeSmtp":
        return self

    def __exit__(self, *args: object) -> None:
        self.calls.append("quit")

    def starttls(self) -> None:
        self.calls.append("starttls")

    def login(self, username: str, password: str) -> None:
        self.calls.append(f"login:{username}")

    def send_message(self, message: EmailMessage) -> None:
        self.calls.append(f"send:{message['To']}")


def test_smtp_sender_uses_tls_and_login(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("smtplib.SMTP", FakeSmtp)
    FakeSmtp.instances.clear()
    sender = SmtpEmailSender("smtp.test", 587, username="user", password="secret", use_tls=True)
    message = EmailMessage()
    message["To"] = "family@test.dev"

    sender.send(message)

    smtp = FakeSmtp.instances[0]
    assert (smtp.host, smtp.port) == ("smtp.test", 587)
    assert smtp.calls == ["starttls", "login:user", "send:family@test.dev", "quit"]
