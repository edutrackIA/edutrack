import io
from datetime import date

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import Attendance, AttendanceStatus, Grade, ImportJob, Student
from app.services import import_service
from tests.conftest import School, auth

URL = "/api/v1/imports"

STUDENTS_HEADER = "code,first_name,last_name,birth_date,sex,year,grade,section\n"


def upload(
    client: TestClient,
    school: School,
    kind: str,
    content: bytes,
    filename: str = "data.csv",
    period_id: int | None = None,
):
    data = {"kind": kind}
    if period_id is not None:
        data["period_id"] = str(period_id)
    return client.post(
        URL,
        data=data,
        files={"file": (filename, content)},
        headers=auth(school.analyst),
    )


def xlsx(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


# --- Estudiantes -----------------------------------------------------------


def test_import_students_creates_and_updates(
    client: TestClient, school: School, db_session: Session
) -> None:
    content = (
        STUDENTS_HEADER
        + "N001,Rosa,Quispe Mamani,2012-02-01,F,2026,3,A\n"
        + "A001,Lucía,Flores Ruiz,2012-05-10,F,2026,3,B\n"
    ).encode()

    response = upload(client, school, "STUDENTS", content)

    assert response.status_code == 202
    body = response.json()
    assert (body["status"], body["rows_ok"], body["rows_failed"]) == ("DONE", 2, 0)
    created = db_session.scalar(select(Student).where(Student.code == "N001"))
    assert created is not None
    assert created.classroom_id == school.classroom_a.id
    assert school.student_a.classroom_id == school.classroom_b.id
    assert school.student_a.last_name == "Flores Ruiz"


def test_import_accepts_semicolons_cp1252_and_local_dates(
    client: TestClient, school: School
) -> None:
    content = (
        "code;first_name;last_name;birth_date;sex;year;grade;section\n"
        "N002;José;Núñez;15/08/2012;m;2026;3;a\n"
    ).encode("cp1252")

    response = upload(client, school, "STUDENTS", content)

    assert response.json()["rows_ok"] == 1


def test_import_reports_row_errors_and_keeps_valid_rows(client: TestClient, school: School) -> None:
    content = (
        STUDENTS_HEADER
        + "N003,Ana,Ok,2012-01-01,F,2026,3,A\n"
        + "N004,Bad,Room,2012-01-01,F,2026,3,Z\n"
        + "X001,Taken,Code,2012-01-01,F,2026,3,A\n"
        + "N005,Bad,Sex,2012-01-01,X,2026,3,A\n"
        + "N006,Bad,Date,2012-31-01,F,2026,3,A\n"
    ).encode()

    body = upload(client, school, "STUDENTS", content).json()

    assert (body["status"], body["rows_ok"], body["rows_failed"]) == ("DONE", 1, 4)
    assert [(e["row"], e["column"]) for e in body["errors"]] == [
        (3, "section"),
        (4, "code"),
        (5, "sex"),
        (6, "birth_date"),
    ]


# --- Notas -----------------------------------------------------------------


def test_import_grades_from_excel(client: TestClient, school: School, db_session: Session) -> None:
    content = xlsx(
        [
            ["student_code", "subject", "score"],
            ["A001", "matemática", 15.5],
            ["A002", "Comunicación", "12,5"],
            ["A002", "Arte", 14],
            ["B001", "Matemática", 25],
        ]
    )

    response = upload(client, school, "GRADES", content, "notas.xlsx", school.period.id)

    body = response.json()
    assert (body["rows_ok"], body["rows_failed"]) == (2, 2)
    assert {e["column"] for e in body["errors"]} == {"subject", "score"}
    scores = db_session.scalars(select(Grade.score).order_by(Grade.score)).all()
    assert scores == [12.5, 15.5]


def test_grade_import_updates_existing_grade(
    client: TestClient, school: School, db_session: Session
) -> None:
    header = "student_code,subject,score\n"
    upload(
        client,
        school,
        "GRADES",
        f"{header}A001,Matemática,10\n".encode(),
        period_id=school.period.id,
    )
    upload(
        client,
        school,
        "GRADES",
        f"{header}A001,Matemática,18\n".encode(),
        period_id=school.period.id,
    )

    assert db_session.scalars(select(Grade.score)).all() == [18.0]


def test_grade_import_requires_a_valid_period(client: TestClient, school: School) -> None:
    content = b"student_code,subject,score\nA001,Matematica,10\n"

    missing = upload(client, school, "GRADES", content)
    foreign = upload(client, school, "GRADES", content, period_id=school.foreign_period.id)

    assert missing.status_code == 422
    assert foreign.status_code == 422


def test_grade_import_rejects_students_from_another_institution(
    client: TestClient, school: School
) -> None:
    content = b"student_code,subject,score\nX001,Matem\xc3\xa1tica,10\n"

    body = upload(client, school, "GRADES", content, period_id=school.period.id).json()

    assert body["status"] == "FAILED"
    assert body["errors"][0]["column"] == "student_code"


# --- Asistencia ------------------------------------------------------------


def test_import_attendance_with_spanish_statuses(
    client: TestClient, school: School, db_session: Session
) -> None:
    content = (
        b"student_code,date,status\n"
        b"A001,2026-03-10,falta\n"
        b"A001,2026-03-11,Tardanza\n"
        b"A001,2026-03-10,PRESENT\n"
        b"A002,2026-03-10,sick\n"
    )

    body = upload(client, school, "ATTENDANCE", content).json()

    assert (body["rows_ok"], body["rows_failed"]) == (2, 2)
    assert body["errors"][0]["message"].startswith("Fila repetida: ya aparece en la fila ")
    records = db_session.scalars(select(Attendance).order_by(Attendance.date)).all()
    assert [(r.date, r.status) for r in records] == [
        (date(2026, 3, 10), AttendanceStatus.ABSENT),
        (date(2026, 3, 11), AttendanceStatus.LATE),
    ]


# --- Archivo ---------------------------------------------------------------


def test_missing_columns_fail_the_import(client: TestClient, school: School) -> None:
    body = upload(client, school, "ATTENDANCE", b"student_code,date\nA001,2026-03-10\n").json()

    assert body["status"] == "FAILED"
    assert body["errors"] == [{"row": 1, "column": "status", "message": "Falta la columna"}]


@pytest.mark.parametrize(
    ("content", "filename"),
    [(b"", "empty.csv"), (b"code,first_name\n", "header.csv"), (b"not excel", "bad.xlsx")],
)
def test_unreadable_or_empty_files_fail(
    client: TestClient, school: School, content: bytes, filename: str
) -> None:
    body = upload(client, school, "STUDENTS", content, filename).json()

    assert body["status"] == "FAILED"
    assert body["rows_ok"] == 0


def test_unsupported_file_type_is_rejected(client: TestClient, school: School) -> None:
    response = upload(client, school, "STUDENTS", b"data", "notes.pdf")

    assert response.status_code == 415


def test_large_files_are_rejected(
    client: TestClient, school: School, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(import_service, "MAX_UPLOAD_BYTES", 10)

    response = upload(client, school, "STUDENTS", b"x" * 50)

    assert response.status_code == 413


def test_too_many_rows_fail_the_import(
    client: TestClient, school: School, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(import_service, "MAX_ROWS", 1)
    content = STUDENTS_HEADER + "N1,A,B,2012-01-01,F,2026,3,A\nN2,A,B,2012-01-01,F,2026,3,A\n"

    body = upload(client, school, "STUDENTS", content.encode()).json()

    assert body["status"] == "FAILED"


# --- Acceso y consulta -----------------------------------------------------


def test_only_analysts_can_import(client: TestClient, school: School) -> None:
    response = client.post(
        URL,
        data={"kind": "STUDENTS"},
        files={"file": ("data.csv", STUDENTS_HEADER.encode())},
        headers=auth(school.director),
    )

    assert response.status_code == 403


def test_get_import_job(client: TestClient, school: School) -> None:
    job_id = upload(client, school, "STUDENTS", STUDENTS_HEADER.encode()).json()["id"]

    found = client.get(f"{URL}/{job_id}", headers=auth(school.analyst))
    missing = client.get(f"{URL}/9999", headers=auth(school.analyst))

    assert found.status_code == 200
    assert found.json()["id"] == job_id
    assert missing.status_code == 404


def test_download_template(client: TestClient, school: School) -> None:
    response = client.get(f"{URL}/templates/GRADES", headers=auth(school.analyst))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.startswith("student_code,subject,score")


def test_preview_validates_without_saving(
    client: TestClient, school: School, db_session: Session
) -> None:
    content = "student_code,subject,score\nA001,Matemática,15\nA001,Física,12\n".encode()

    response = client.post(
        URL,
        data={"kind": "GRADES", "period_id": str(school.period.id), "dry_run": "true"},
        files={"file": ("notas.csv", content, "text/csv")},
        headers=auth(school.analyst),
    )

    body = response.json()
    assert body["preview"] is True
    assert body["id"] is None
    assert (body["rows_ok"], body["rows_failed"]) == (1, 1)
    assert db_session.scalars(select(Grade)).all() == []
    assert db_session.scalars(select(ImportJob)).all() == []
