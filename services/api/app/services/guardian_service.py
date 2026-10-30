from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.domain import Guardianship, Student, User
from app.repositories.student_repository import StudentRepository
from app.schemas.guardian import GuardianInput, GuardianResponse
from app.services.access_policy import AccessPolicy
from app.services.guardian_links import GuardianLinkError, link_guardian
from app.services.invitation_service import InvitationService
from app.services.notifications.email_sender import EmailSender


class GuardianService:
    def __init__(self, db: Session, sender: EmailSender) -> None:
        self.db = db
        self.students = StudentRepository(db)
        self.policy = AccessPolicy(db)
        self.invitations = InvitationService(db, sender)

    def list(self, user: User, student_id: int) -> list[GuardianResponse]:
        student = self._student(user, student_id)
        rows = self.db.execute(
            select(User, Guardianship.kinship)
            .join(Guardianship, Guardianship.guardian_id == User.id)
            .where(Guardianship.student_id == student.id)
            .order_by(User.full_name)
        ).all()
        return [GuardianResponse.from_model(guardian, kinship) for guardian, kinship in rows]

    def add(self, user: User, student_id: int, data: GuardianInput) -> GuardianResponse:
        student = self._student(user, student_id)
        try:
            link = link_guardian(
                self.db, student, full_name=data.full_name, email=data.email, kinship=data.kinship
            )
        except GuardianLinkError as exc:
            if exc.invalid_input:
                raise UnprocessableError(exc.message) from exc
            raise ConflictError(exc.message, code="GUARDIAN_CONFLICT") from exc
        self.db.commit()

        sent = None if link.user.has_access else self.invitations.invite(link.user)
        kinship = self.db.get(Guardianship, (link.user.id, student.id)).kinship
        return GuardianResponse.from_model(link.user, kinship, invitation_sent=sent)

    def unlink(self, user: User, student_id: int, guardian_id: int) -> None:
        student = self._student(user, student_id)
        link = self._link(guardian_id, student.id)
        self.db.delete(link)
        self.db.commit()

    def resend(self, user: User, student_id: int, guardian_id: int) -> GuardianResponse:
        student = self._student(user, student_id)
        link = self._link(guardian_id, student.id)
        guardian = self.db.get(User, guardian_id)
        sent = self.invitations.invite(guardian)
        return GuardianResponse.from_model(guardian, link.kinship, invitation_sent=sent)

    def _student(self, user: User, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        self.policy.ensure_can_manage_guardians(user, student)
        return student

    def _link(self, guardian_id: int, student_id: int) -> Guardianship:
        link = self.db.get(Guardianship, (guardian_id, student_id))
        if link is None:
            raise NotFoundError("Guardian not linked to this student")
        return link
