"""Weekly check-in reminders for tutors and escalation to the director."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import week_deadline, week_start
from app.domain import Classroom, Role, User
from app.repositories.messaging_repository import MessagingRepository
from app.repositories.situation_repository import SituationRepository
from app.services.notifications.delivery import deliver
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import StaffNoticeEmail

# fmt: off
MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
# fmt: on


def _label(classroom: Classroom) -> str:
    return f"{classroom.grade}° {classroom.section}"


def _date(value: date) -> str:
    return f"{value.day} de {MONTHS[value.month - 1]}"


class _Notifier:
    def __init__(self, db: Session, sender: EmailSender) -> None:
        self.db = db
        self.sender = sender
        self.log = MessagingRepository(db)

    def notify(
        self, user: User, *, kind: str, reference: str, subject: str, paragraphs: list[str]
    ) -> bool:
        if self.log.already_notified(kind=kind, recipient_id=user.id, reference=reference):
            return False
        email = StaffNoticeEmail(
            recipient_name=user.full_name.split()[0],
            subject=subject,
            paragraphs=paragraphs,
            portal_url=f"{get_settings().portal_url}/seguimiento",
        )
        if not deliver(
            self.sender, to=user.email, subject=subject, text=email.text(), html=email.html()
        ):
            return False
        self.log.log_notice(kind=kind, recipient_id=user.id, reference=reference)
        return True


def _pending(db: Session, start: date) -> list[Classroom]:
    checkins = SituationRepository(db)
    classrooms = db.scalars(select(Classroom).where(Classroom.tutor_id.is_not(None))).all()
    return [
        classroom
        for classroom in classrooms
        if checkins.get_checkin(classroom_id=classroom.id, week_start=start) is None
    ]


def remind_pending_checkins(db: Session, sender: EmailSender, today: date) -> int:
    """Friday: remind tutors who have not confirmed the weekly follow-up yet."""
    start = week_start(today)
    deadline = week_deadline(start)
    notifier = _Notifier(db, sender)
    sent = 0
    for classroom in _pending(db, start):
        sent += notifier.notify(
            classroom.tutor,
            kind="CHECKIN_REMINDER",
            reference=f"{classroom.id}:{start.isoformat()}",
            subject=f"Recordatorio: seguimiento semanal de {_label(classroom)}",
            paragraphs=[
                f"Aún no confirmaste el seguimiento semanal de {_label(classroom)}.",
                f"Puedes completarlo hasta el sábado {_date(deadline)}. Solo marca a los "
                "estudiantes con cambios y confirma el resto.",
            ],
        )
    db.commit()
    return sent


def report_missed_checkins(db: Session, sender: EmailSender, today: date) -> int:
    """Sunday: tell tutors the week closed without follow-up; after 2 weeks, the director."""
    start = week_start(today)
    previous = start - timedelta(days=7)
    checkins = SituationRepository(db)
    notifier = _Notifier(db, sender)
    sent = 0

    for classroom in _pending(db, start):
        week = f"semana del {_date(start)} al {_date(week_deadline(start))}"
        sent += notifier.notify(
            classroom.tutor,
            kind="CHECKIN_MISSED",
            reference=f"{classroom.id}:{start.isoformat()}",
            subject=f"Seguimiento no completado: {_label(classroom)}",
            paragraphs=[
                f"El seguimiento semanal de {_label(classroom)} de la {week} no se completó.",
                "El de la próxima semana se abre el lunes.",
            ],
        )
        if checkins.get_checkin(classroom_id=classroom.id, week_start=previous) is not None:
            continue
        directors = db.scalars(
            select(User).where(
                User.institution_id == classroom.institution_id,
                User.role == Role.DIRECTOR,
                User.is_active.is_(True),
            )
        ).all()
        for director in directors:
            sent += notifier.notify(
                director,
                kind="CHECKIN_ESCALATION",
                reference=f"{classroom.id}:{start.isoformat()}",
                subject=f"Dos semanas sin seguimiento en {_label(classroom)}",
                paragraphs=[
                    f"{classroom.tutor.full_name}, tutor de {_label(classroom)}, no completó el "
                    "seguimiento semanal en las dos últimas semanas.",
                    "Le sugerimos conversar con el tutor para conocer el motivo.",
                ],
            )
    db.commit()
    return sent
