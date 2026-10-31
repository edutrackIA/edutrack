"""Consent to the privacy notice and data subject rights requests (Ley N.° 29733)."""

from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from app.core.privacy import PRIVACY_NOTICE_VERSION, RESPONSE_BUSINESS_DAYS
from app.core.time import utcnow
from app.domain import (
    Attendance,
    BehaviorRecord,
    Commitment,
    DataRequest,
    DataRequestStatus,
    FamilyCheckin,
    FamilySurvey,
    Grade,
    PrivacyConsent,
    Recommendation,
    RiskAssessment,
    Role,
    StudentSituation,
    User,
)
from app.repositories.student_repository import StudentRepository
from app.schemas.privacy import DataRequestInput, DataRequestResolution, DataRequestResponse
from app.services.access_policy import AccessPolicy
from app.services.notifications.delivery import deliver
from app.services.notifications.email_sender import EmailSender
from app.services.notifications.templates import StaffNoticeEmail

KIND_LABELS = {
    "ACCESS": "acceso a sus datos",
    "RECTIFICATION": "rectificación de datos",
    "CANCELLATION": "cancelación de datos",
    "OPPOSITION": "oposición al tratamiento",
}


def add_business_days(start: date, days: int) -> date:
    """Weekdays only; public holidays are not counted here."""
    current = start
    while days > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:
            days -= 1
    return current


class PrivacyService:
    def __init__(self, db: Session, sender: EmailSender | None = None) -> None:
        self.db = db
        self.sender = sender
        self.policy = AccessPolicy(db)

    # --- Consentimiento -----------------------------------------------------------------

    def consent(self, user: User) -> PrivacyConsent | None:
        return self.db.scalar(
            select(PrivacyConsent).where(
                PrivacyConsent.user_id == user.id,
                PrivacyConsent.notice_version == PRIVACY_NOTICE_VERSION,
            )
        )

    def accept(self, user: User, version: str) -> PrivacyConsent:
        if version != PRIVACY_NOTICE_VERSION:
            raise ConflictError(
                "The privacy notice changed; read the current version", code="NOTICE_OUTDATED"
            )
        existing = self.consent(user)
        if existing is not None:
            return existing
        consent = PrivacyConsent(user_id=user.id, notice_version=version)
        self.db.add(consent)
        self.db.commit()
        return consent

    def ensure_consent(self, user: User) -> None:
        """Guardians must accept the current notice before sending any data."""
        if user.role == Role.PARENT and self.consent(user) is None:
            raise ForbiddenError("Accept the privacy notice first", code="CONSENT_REQUIRED")

    # --- Solicitudes ARCO -------------------------------------------------------------

    def create_request(self, user: User, data: DataRequestInput) -> DataRequestResponse:
        student = StudentRepository(self.db).get(data.student_id)
        if student is None:
            raise NotFoundError("Student not found")
        self.policy.ensure_is_guardian(user, student)
        request = DataRequest(
            institution_id=user.institution_id,
            requester_id=user.id,
            student_id=student.id,
            kind=data.kind,
            details=data.details.strip(),
        )
        self.db.add(request)
        self.db.commit()
        self._notify_direction(request)
        return self._response(request)

    def list_requests(self, user: User) -> list[DataRequestResponse]:
        query = select(DataRequest).where(DataRequest.institution_id == user.institution_id)
        if user.role == Role.PARENT:
            query = query.where(DataRequest.requester_id == user.id)
        elif user.role != Role.DIRECTOR:
            raise ForbiddenError("You do not have access to this resource")
        requests = self.db.scalars(query.order_by(DataRequest.created_at.desc())).all()
        return [self._response(request) for request in requests]

    def resolve(
        self, user: User, request_id: int, data: DataRequestResolution
    ) -> DataRequestResponse:
        request = self.db.get(DataRequest, request_id)
        if request is None or request.institution_id != user.institution_id:
            raise NotFoundError("Request not found")
        if request.status != DataRequestStatus.PENDING:
            raise ConflictError("The request was already answered")
        if data.status == DataRequestStatus.PENDING:
            raise UnprocessableError("Choose resolved or rejected")
        request.status = data.status
        request.response = data.response.strip()
        request.resolved_at = utcnow()
        request.resolved_by = user.id
        self.db.commit()
        self._notify_requester(request)
        return self._response(request)

    # --- Expediente para el derecho de acceso ----------------------------------------------

    def export_student(self, user: User, student_id: int) -> dict[str, Any]:
        """Every record EduTrack keeps about a student, for an access request."""
        student = StudentRepository(self.db).get(student_id)
        if student is None or student.institution_id != user.institution_id:
            raise NotFoundError("Student not found")

        def rows(model: Any, *columns: str) -> list[dict[str, Any]]:
            items = self.db.scalars(select(model).where(model.student_id == student.id)).all()
            return [{column: _plain(getattr(item, column)) for column in columns} for item in items]

        return {
            "generated_at": utcnow().isoformat(),
            "notice_version": PRIVACY_NOTICE_VERSION,
            "student": {
                "code": student.code,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "birth_date": student.birth_date.isoformat(),
                "sex": _plain(student.sex),
                "classroom": f"{student.classroom.label} ({student.classroom.year})",
                "status": _plain(student.status),
                "exit_date": _plain(student.exit_date),
                "exit_reason": _plain(student.exit_reason),
            },
            "guardians": [
                {"full_name": guardian.full_name, "email": guardian.email}
                for guardian in student.guardians
            ],
            "grades": [
                {"subject": grade.subject.name, "period_id": grade.period_id, "score": grade.score}
                for grade in self.db.scalars(select(Grade).where(Grade.student_id == student.id))
            ],
            "attendance": rows(Attendance, "date", "status"),
            "behavior": rows(BehaviorRecord, "period_id", "rating", "notes"),
            "family_surveys": rows(
                FamilySurvey,
                "period_id",
                "study_hours_week",
                "parent_education",
                "home_internet",
                "has_study_device",
                "family_communication",
                "student_works",
                "household_size",
            ),
            "family_checkins": rows(
                FamilyCheckin, "month", "mood", "home_changes", "peer_concern", "comment"
            ),
            "risk_assessments": rows(
                RiskAssessment, "period_id", "probability", "level", "model_version", "created_at"
            ),
            "recommendations": rows(
                Recommendation, "period_id", "status", "parent_items", "sent_at"
            ),
            "commitments": rows(Commitment, "meeting_date", "agreements", "status"),
            "context_situations": rows(
                StudentSituation, "kind", "note", "started_on", "resolved_on"
            ),
        }

    # --- Internos ------------------------------------------------------------------------

    def _response(self, request: DataRequest) -> DataRequestResponse:
        due = add_business_days(request.created_at.date(), RESPONSE_BUSINESS_DAYS)
        return DataRequestResponse.from_model(request, due)

    def _notify_direction(self, request: DataRequest) -> None:
        if self.sender is None:
            return
        directors = self.db.scalars(
            select(User).where(
                User.institution_id == request.institution_id,
                User.role == Role.DIRECTOR,
                User.is_active.is_(True),
            )
        ).all()
        due = add_business_days(request.created_at.date(), RESPONSE_BUSINESS_DAYS)
        for director in directors:
            email = StaffNoticeEmail(
                recipient_name=director.full_name.split()[0],
                subject=f"Nueva solicitud de {KIND_LABELS[request.kind]}",
                paragraphs=[
                    f"{request.requester.full_name} pidió {KIND_LABELS[request.kind]} sobre "
                    f"{request.student.full_name}.",
                    f"Por ley debe responderse a más tardar el {due:%d/%m/%Y}.",
                ],
                portal_url=f"{get_settings().portal_url}/solicitudes-de-datos",
            )
            deliver(
                self.sender,
                to=director.email,
                subject=email.subject,
                text=email.text(),
                html=email.html(),
            )

    def _notify_requester(self, request: DataRequest) -> None:
        if self.sender is None:
            return
        outcome = (
            "fue atendida" if request.status == DataRequestStatus.RESOLVED else "fue rechazada"
        )
        email = StaffNoticeEmail(
            recipient_name=request.requester.full_name.split()[0],
            subject=f"Tu solicitud de {KIND_LABELS[request.kind]} {outcome}",
            paragraphs=[
                f"Tu solicitud de {KIND_LABELS[request.kind]} sobre "
                f"{request.student.full_name} {outcome}.",
                f"Respuesta del colegio: {request.response}",
            ],
            portal_url=f"{get_settings().portal_url}/mi-cuenta",
        )
        deliver(
            self.sender,
            to=request.requester.email,
            subject=email.subject,
            text=email.text(),
            html=email.html(),
        )


def _plain(value: Any) -> Any:
    """JSON-friendly values: dates as ISO text and enums as their names."""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value
