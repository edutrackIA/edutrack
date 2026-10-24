from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.domain import Institution, RiskLevel, User
from app.services.dashboard_service import DashboardService, period_label
from app.services.reports.risk_report import ReportRow, RiskReport, render_risk_report
from app.services.risk.features import FEATURE_LABELS


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.dashboard = DashboardService(db)

    def build_risk_report(
        self, user: User, period_id: int | None, classroom_id: int | None
    ) -> RiskReport:
        data = self.dashboard.load(user, period_id, classroom_id)
        rows = [
            ReportRow(
                code=student.code,
                name=student.full_name,
                classroom=student.classroom.label,
                level=assessment.level,
                probability=assessment.probability,
                factors=[
                    FEATURE_LABELS.get(factor["feature"], factor["feature"])
                    for factor in assessment.top_factors[:3]
                ],
            )
            for student in data.students
            if (assessment := data.assessments.get(student.id)) is not None
        ]
        rows.sort(key=lambda row: (-row.probability, row.name))

        by_level = dict.fromkeys(RiskLevel, 0)
        for row in rows:
            by_level[row.level] += 1

        institution = self.db.get(Institution, user.institution_id)
        scope = (
            f"Aula {data.students[0].classroom.label}"
            if classroom_id is not None and data.students
            else "Toda la institución"
        )
        return RiskReport(
            institution=institution.name if institution else "EduTrack",
            period=period_label(data.period) if data.period else "Sin periodo evaluado",
            scope=scope,
            generated_at=utcnow(),
            by_level=by_level,
            rows=rows,
            not_evaluated=len(data.students) - len(rows),
        )

    def risk_report_pdf(
        self, user: User, period_id: int | None, classroom_id: int | None
    ) -> tuple[str, bytes]:
        report = self.build_risk_report(user, period_id, classroom_id)
        slug = report.period.replace(" · ", "-").replace(" ", "-").lower()
        filename = f"reporte-riesgo-{slug}.pdf"
        return filename, render_risk_report(report)
