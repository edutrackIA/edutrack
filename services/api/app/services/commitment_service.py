from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, UnprocessableError
from app.domain import Commitment, Student, User
from app.repositories.commitment_repository import CommitmentRepository
from app.repositories.student_repository import StudentRepository
from app.schemas.commitment import CommitmentInput, CommitmentUpdate
from app.services.access_policy import AccessPolicy


class CommitmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.commitments = CommitmentRepository(db)
        self.students = StudentRepository(db)
        self.policy = AccessPolicy(db)

    def list_for_student(self, user: User, student_id: int) -> list[Commitment]:
        student = self._get_student(student_id)
        self.policy.ensure_can_view_commitments(user, student)
        return self.commitments.list_for_student(student.id)

    def create(self, user: User, student_id: int, data: CommitmentInput) -> Commitment:
        student = self._get_student(student_id)
        self.policy.ensure_can_manage_commitments(user, student)
        if not self.students.is_guardian(guardian_id=data.guardian_id, student_id=student.id):
            raise UnprocessableError("The guardian is not registered for this student")

        commitment = self.commitments.add(
            Commitment(student_id=student.id, tutor_id=user.id, **data.model_dump())
        )
        self.db.commit()
        return commitment

    def update(
        self, user: User, student_id: int, commitment_id: int, data: CommitmentUpdate
    ) -> Commitment:
        student = self._get_student(student_id)
        self.policy.ensure_can_manage_commitments(user, student)
        commitment = self.commitments.get(commitment_id)
        if commitment is None or commitment.student_id != student.id:
            raise NotFoundError("Commitment not found")

        changes = data.model_dump(exclude_unset=True, exclude_none=True)
        follow_up = changes.get("follow_up_date", commitment.follow_up_date)
        if follow_up is not None and follow_up < commitment.meeting_date:
            raise UnprocessableError("follow_up_date must be on or after meeting_date")
        for field, value in changes.items():
            setattr(commitment, field, value)

        self.db.commit()
        return commitment

    def _get_student(self, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        return student
