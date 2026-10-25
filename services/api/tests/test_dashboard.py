from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain import RiskLevel
from app.services.report_service import ReportService
from app.services.reports.risk_report import render_risk_report
from tests.conftest import School, auth

SUMMARY_URL = "/api/v1/dashboard/summary"
REPORT_URL = "/api/v1/reports/risk"


# --- Dashboard -------------------------------------------------------------


def test_director_dashboard_summary(client: TestClient, assessed_school: School) -> None:
    school = assessed_school

    response = client.get(SUMMARY_URL, headers=auth(school.director))

    assert response.status_code == 200
    body = response.json()
    assert body["period_id"] == school.period.id
    assert body["period_label"] == "2026 · Bimestre 1"
    assert body["total_students"] == 3
    assert body["evaluated_students"] == 2
    assert body["by_level"] == {"LOW": 1, "MEDIUM": 0, "HIGH": 1}
    assert body["by_classroom"] == [
        {
            "classroom_id": school.classroom_a.id,
            "label": "3° A",
            "evaluated": 2,
            "low": 1,
            "medium": 0,
            "high": 1,
        },
        {
            "classroom_id": school.classroom_b.id,
            "label": "3° B",
            "evaluated": 0,
            "low": 0,
            "medium": 0,
            "high": 0,
        },
    ]
    assert body["top_factors"] == [{"feature": "avg_score", "label": "Promedio", "frequency": 1}]


def test_dashboard_without_assessments(client: TestClient, school: School) -> None:
    body = client.get(SUMMARY_URL, headers=auth(school.analyst)).json()

    assert body["period_id"] is None
    assert body["evaluated_students"] == 0
    assert body["total_students"] == 3


def test_dashboard_for_explicit_period(client: TestClient, assessed_school: School) -> None:
    school = assessed_school

    body = client.get(
        f"{SUMMARY_URL}?period_id={school.period.id}", headers=auth(school.director)
    ).json()
    foreign = client.get(
        f"{SUMMARY_URL}?period_id={school.foreign_period.id}", headers=auth(school.director)
    )

    assert body["evaluated_students"] == 2
    assert foreign.status_code == 422


def test_dashboard_is_for_management_only(client: TestClient, assessed_school: School) -> None:
    for user in (assessed_school.teacher, assessed_school.parent):
        assert client.get(SUMMARY_URL, headers=auth(user)).status_code == 403


# --- Reporte PDF -----------------------------------------------------------


def test_report_rows_are_sorted_by_probability(
    assessed_school: School, db_session: Session
) -> None:
    school = assessed_school

    report = ReportService(db_session).build_risk_report(school.director, None, None)

    assert [row.code for row in report.rows] == ["A001", "A002"]
    assert report.rows[0].level == RiskLevel.HIGH
    assert report.rows[0].factors == ["Promedio"]
    assert report.rows[1].factors == []
    assert report.not_evaluated == 1
    assert report.scope == "Toda la institución"


def test_report_can_be_scoped_to_a_classroom(assessed_school: School, db_session: Session) -> None:
    school = assessed_school

    report = ReportService(db_session).build_risk_report(
        school.director, school.period.id, school.classroom_b.id
    )

    assert report.rows == []
    assert report.not_evaluated == 1
    assert report.scope == "Aula 3° B"


def test_director_downloads_pdf_report(client: TestClient, assessed_school: School) -> None:
    response = client.get(REPORT_URL, headers=auth(assessed_school.director))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert (
        'filename="reporte-riesgo-2026-bimestre-1.pdf"' in response.headers["content-disposition"]
    )


def test_report_renders_without_assessments(school: School, db_session: Session) -> None:
    report = ReportService(db_session).build_risk_report(school.analyst, None, None)

    assert report.period == "Sin periodo evaluado"
    assert render_risk_report(report).startswith(b"%PDF")


def test_report_validates_classroom_and_role(client: TestClient, assessed_school: School) -> None:
    school = assessed_school

    foreign = client.get(
        f"{REPORT_URL}?classroom_id={school.foreign_classroom.id}", headers=auth(school.director)
    )
    teacher = client.get(REPORT_URL, headers=auth(school.teacher))

    assert foreign.status_code == 422
    assert teacher.status_code == 403
