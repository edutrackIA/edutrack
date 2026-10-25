from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.domain import RiskLevel

LEVEL_LABELS = {RiskLevel.LOW: "Bajo", RiskLevel.MEDIUM: "Moderado", RiskLevel.HIGH: "Alto"}
LEVEL_COLORS = {
    RiskLevel.LOW: colors.HexColor("#d1fae5"),
    RiskLevel.MEDIUM: colors.HexColor("#fef3c7"),
    RiskLevel.HIGH: colors.HexColor("#fee2e2"),
}
BRAND = colors.HexColor("#1168bd")
REPORT_NOTICE = (
    "Documento confidencial de uso interno. Los niveles de riesgo son estimaciones de un "
    "modelo de Machine Learning y deben interpretarse junto con el criterio del tutor. "
    "No comparta este reporte con las familias."
)


@dataclass
class ReportRow:
    code: str
    name: str
    classroom: str
    level: RiskLevel
    probability: float
    factors: list[str]


@dataclass
class RiskReport:
    institution: str
    period: str
    scope: str
    generated_at: datetime
    by_level: dict[RiskLevel, int]
    rows: list[ReportRow]
    not_evaluated: int


def render_risk_report(report: RiskReport) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
        title=f"Reporte de riesgo - {report.period}",
        author="EduTrack",
    )
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8, leading=10)

    story = [
        Paragraph("Reporte de riesgo académico", styles["Title"]),
        Paragraph(
            f"{escape(report.institution)} · {escape(report.period)} · {escape(report.scope)}",
            styles["Heading3"],
        ),
        Spacer(1, 0.4 * cm),
        _summary_table(report),
        Spacer(1, 0.6 * cm),
    ]
    if report.rows:
        story.append(_students_table(report.rows, small))
    else:
        story.append(Paragraph("No hay estudiantes evaluados en este periodo.", styles["BodyText"]))
    story += [Spacer(1, 0.6 * cm), Paragraph(REPORT_NOTICE, small)]

    def footer(canvas: Canvas, doc: SimpleDocTemplate) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        generated = report.generated_at.strftime("%d/%m/%Y %H:%M")
        canvas.drawString(1.5 * cm, 1 * cm, f"EduTrack · Generado el {generated} UTC")
        canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def _summary_table(report: RiskReport) -> Table:
    data = [["Nivel", "Estudiantes"]]
    data += [[LEVEL_LABELS[level], str(report.by_level[level])] for level in reversed(RiskLevel)]
    data.append(["Sin evaluar", str(report.not_evaluated)])
    table = Table(data, colWidths=[5 * cm, 3 * cm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
    ]
    for index, level in enumerate(reversed(RiskLevel), start=1):
        style.append(("BACKGROUND", (0, index), (0, index), LEVEL_COLORS[level]))
    table.setStyle(TableStyle(style))
    return table


def _students_table(rows: list[ReportRow], style: ParagraphStyle) -> Table:
    data: list[list[object]] = [
        ["Código", "Estudiante", "Aula", "Nivel", "Prob.", "Factores principales"]
    ]
    for row in rows:
        data.append(
            [
                row.code,
                Paragraph(escape(row.name), style),
                row.classroom,
                LEVEL_LABELS[row.level],
                f"{row.probability:.0%}",
                Paragraph(escape(", ".join(row.factors)), style),
            ]
        )
    table = Table(
        data,
        colWidths=[2.2 * cm, 4.8 * cm, 1.5 * cm, 2 * cm, 1.4 * cm, 6 * cm],
        repeatRows=1,
    )
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for index, row in enumerate(rows, start=1):
        style_commands.append(("BACKGROUND", (3, index), (3, index), LEVEL_COLORS[row.level]))
    table.setStyle(TableStyle(style_commands))
    return table
