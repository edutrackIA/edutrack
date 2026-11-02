import re

from fastapi.testclient import TestClient

from tests.conftest import Outbox, School, auth


def url(school: School) -> str:
    return f"/api/v1/students/{school.student_a2.id}/guardians"


def add(client: TestClient, school: School, **overrides: str):
    body = {
        "full_name": "Rosa Huamán Flores",
        "email": "Rosa.Huaman@Correo.com",
        "kinship": "Madre",
    }
    return client.post(url(school), json=body | overrides, headers=auth(school.director))


def invitation_link(outbox: Outbox, index: int = -1) -> str:
    text = outbox.messages[index].get_body(("plain",)).get_content()
    match = re.search(r"/invitacion/(\S+)", text)
    assert match is not None
    return match.group(1)


def test_director_registers_a_new_guardian_and_invites_them(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    response = add(client, school)

    body = response.json()
    assert response.status_code == 201
    assert body["email"] == "rosa.huaman@correo.com"
    assert body["kinship"] == "Madre"
    assert body["has_access"] is False
    assert body["invitation_sent"] is True
    assert [message["To"] for message in outbox.messages] == ["rosa.huaman@correo.com"]
    assert "Mateo" in outbox.messages[0].get_body(("plain",)).get_content()
    assert invitation_link(outbox)


def test_an_existing_parent_is_linked_without_a_new_invitation(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    response = add(client, school, email="parent@school.dev", full_name="Otro nombre")

    assert response.status_code == 201
    assert response.json()["id"] == school.parent.id
    assert response.json()["has_access"] is True
    assert response.json()["invitation_sent"] is None
    assert outbox.messages == []


def test_staff_emails_and_invalid_emails_are_rejected(client: TestClient, school: School) -> None:
    staff = add(client, school, email="teacher@school.dev")
    invalid = add(client, school, email="no-es-correo")

    assert staff.status_code == 409
    assert staff.json()["code"] == "GUARDIAN_CONFLICT"
    assert invalid.status_code == 422


def test_only_direction_and_analysis_manage_guardians(client: TestClient, school: School) -> None:
    for user in (school.teacher, school.parent):
        assert client.get(url(school), headers=auth(user)).status_code == 403
    assert client.get(url(school), headers=auth(school.analyst)).status_code == 200


def test_list_and_unlink_guardians(client: TestClient, school: School) -> None:
    guardian = add(client, school).json()

    listed = client.get(url(school), headers=auth(school.director)).json()
    removed = client.delete(f"{url(school)}/{guardian['id']}", headers=auth(school.director))
    again = client.delete(f"{url(school)}/{guardian['id']}", headers=auth(school.director))

    assert [item["full_name"] for item in listed] == ["Rosa Huamán Flores"]
    assert removed.status_code == 204
    assert client.get(url(school), headers=auth(school.director)).json() == []
    assert again.status_code == 404


def test_resending_replaces_the_previous_link(
    client: TestClient, school: School, outbox: Outbox
) -> None:
    guardian = add(client, school).json()
    first = invitation_link(outbox)

    resent = client.post(
        f"{url(school)}/{guardian['id']}/invitation", headers=auth(school.director)
    )
    second = invitation_link(outbox)

    assert resent.json()["invitation_sent"] is True
    assert first != second
    assert client.get(f"/api/v1/invitations/{first}").json()["code"] == "INVITATION_EXPIRED"
    assert client.get(f"/api/v1/invitations/{second}").status_code == 200


def test_guardians_with_access_are_not_invited_again(client: TestClient, school: School) -> None:
    add(client, school, email="parent@school.dev")

    response = client.post(
        f"{url(school)}/{school.parent.id}/invitation", headers=auth(school.director)
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ALREADY_HAS_ACCESS"
