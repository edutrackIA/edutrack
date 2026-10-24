from dataclasses import dataclass
from html import escape

from app.services.recommendations.catalog import ML_DISCLAIMER


@dataclass
class RecommendationEmail:
    guardian_name: str
    student_name: str
    bimester: int
    items: list[str]
    tutor_name: str
    institution_name: str
    portal_url: str

    @property
    def subject(self) -> str:
        return f"Recomendaciones para {self.student_name} — {self.bimester}.° bimestre"

    def text(self) -> str:
        items = "\n".join(f"{index}. {item}" for index, item in enumerate(self.items, start=1))
        return (
            f"Hola, {self.guardian_name}:\n\n"
            f"Queremos compartir algunas sugerencias para apoyar a {self.student_name} "
            f"durante este bimestre:\n\n{items}\n\n"
            f"Puede revisar el avance de {self.student_name} en el portal: {self.portal_url}\n\n"
            f"Saludos,\n{self.tutor_name}\n{self.institution_name}\n\n"
            f"---\n{ML_DISCLAIMER}\n"
        )

    def html(self) -> str:
        items = "".join(
            f'<li style="margin-bottom:10px">{escape(item)}</li>' for item in self.items
        )
        return f"""\
<!doctype html>
<html lang="es">
  <body style="margin:0;padding:24px;background:#f4f6fb;font-family:Arial,sans-serif;color:#1f2937">
    <table role="presentation" width="100%" style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px">
      <tr>
        <td style="padding:24px 28px;background:#1168bd;border-radius:12px 12px 0 0;color:#ffffff">
          <strong style="font-size:20px">EduTrack</strong><br>
          <span style="font-size:14px">{escape(self.institution_name)}</span>
        </td>
      </tr>
      <tr>
        <td style="padding:28px">
          <p>Hola, {escape(self.guardian_name)}:</p>
          <p>Queremos compartir algunas sugerencias para apoyar a
            <strong>{escape(self.student_name)}</strong> durante este bimestre:</p>
          <ol style="padding-left:20px;line-height:1.5">{items}</ol>
          <p style="text-align:center;margin:28px 0">
            <a href="{escape(self.portal_url)}"
               style="background:#1168bd;color:#ffffff;padding:12px 22px;border-radius:8px;text-decoration:none">
              Ver avance en el portal
            </a>
          </p>
          <p>Saludos,<br>{escape(self.tutor_name)}<br>{escape(self.institution_name)}</p>
        </td>
      </tr>
      <tr>
        <td style="padding:16px 28px;background:#f9fafb;border-radius:0 0 12px 12px;font-size:12px;color:#6b7280">
          {escape(ML_DISCLAIMER)}
        </td>
      </tr>
    </table>
  </body>
</html>
"""
