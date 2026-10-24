import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import utcnow
from app.domain import Institution, Recommendation
from app.repositories.academic_repository import AcademicRepository
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import RecommendationEmail

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session, sender: EmailSender) -> None:
        self.db = db
        self.sender = sender
        self.academic = AcademicRepository(db)
        self.settings = get_settings()

    def send_recommendation(self, recommendation: Recommendation) -> bool:
        """Email the approved recommendation to every guardian of the student.

        A delivery failure never undoes the tutor's approval: `sent_at` stays empty
        so the recommendation can be sent again.
        """
        student = recommendation.student
        guardians = [guardian for guardian in student.guardians if guardian.is_active]
        if not guardians:
            return False

        period = self.academic.get_period(recommendation.period_id)
        institution = self.db.get(Institution, student.institution_id)
        tutor = student.classroom.tutor
        try:
            for guardian in guardians:
                email = RecommendationEmail(
                    guardian_name=guardian.full_name.split()[0],
                    student_name=student.first_name,
                    bimester=period.bimester if period else 0,
                    items=recommendation.parent_items,
                    tutor_name=tutor.full_name if tutor else "Tutor",
                    institution_name=institution.name if institution else "EduTrack",
                    portal_url=self.settings.portal_url,
                )
                self.sender.send(self._build(email, guardian.email))
        except (smtplib.SMTPException, OSError):
            logger.warning("Could not send recommendation %s", recommendation.id, exc_info=True)
            return False

        recommendation.sent_at = utcnow()
        self.db.commit()
        return True

    def _build(self, email: RecommendationEmail, recipient: str) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = email.subject
        message["From"] = self.settings.mail_from
        message["To"] = recipient
        message.set_content(email.text())
        message.add_alternative(email.html(), subtype="html")
        return message
