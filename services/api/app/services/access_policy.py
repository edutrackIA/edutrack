from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, NotFoundError
from app.domain import Classroom, Role, Student, User
from app.repositories.classroom_repository import ClassroomRepository
from app.repositories.student_repository import StudentRepository

STAFF_WITH_FULL_ACCESS = {Role.DIRECTOR, Role.ANALYST}


class AccessPolicy:
    """Membership rules: a role grants endpoints, membership grants records."""

    def __init__(self, db: Session) -> None:
        self.classrooms = ClassroomRepository(db)
        self.students = StudentRepository(db)

    def visible_classroom_ids(self, user: User) -> set[int] | None:
        """None means every classroom of the user's institution."""
        if user.role in STAFF_WITH_FULL_ACCESS:
            return None
        if user.role == Role.TEACHER:
            return self.classrooms.teacher_classroom_ids(user.id)
        return set()

    def tutored_ids(self, user: User) -> set[int]:
        if user.role != Role.TEACHER:
            return set()
        return self.classrooms.tutored_classroom_ids(user.id)

    def ensure_can_view_classroom(self, user: User, classroom: Classroom) -> None:
        self._ensure_same_institution(user, classroom.institution_id, "Classroom")
        visible = self.visible_classroom_ids(user)
        if visible is not None and classroom.id not in visible:
            raise self._forbidden()

    def ensure_can_view_student(self, user: User, student: Student) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role in STAFF_WITH_FULL_ACCESS:
            return
        if user.role == Role.TEACHER:
            if student.classroom_id in self.classrooms.teacher_classroom_ids(user.id):
                return
        elif user.role == Role.PARENT and self.students.is_guardian(
            guardian_id=user.id, student_id=student.id
        ):
            return
        raise self._forbidden()

    def ensure_can_view_risk(self, user: User, student: Student) -> None:
        """Families get recommendations, never risk levels or probabilities."""
        if user.role == Role.PARENT:
            self._ensure_same_institution(user, student.institution_id, "Student")
            raise self._forbidden()
        self.ensure_can_view_student(user, student)

    @staticmethod
    def can_see_risk(user: User) -> bool:
        return user.role != Role.PARENT

    def ensure_can_edit_student(self, user: User, student: Student) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role not in STAFF_WITH_FULL_ACCESS:
            raise self._forbidden()

    def ensure_can_record_grade(self, user: User, student: Student, subject_id: int) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role == Role.ANALYST:
            return
        if user.role == Role.TEACHER and self.classrooms.has_assignment(
            classroom_id=student.classroom_id, subject_id=subject_id, teacher_id=user.id
        ):
            return
        raise self._forbidden()

    def ensure_can_record_behavior(self, user: User, student: Student) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role == Role.ANALYST:
            return
        if user.role == Role.TEACHER and student.classroom.tutor_id == user.id:
            return
        raise self._forbidden()

    def ensure_can_submit_survey(self, user: User, student: Student) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role == Role.ANALYST:
            return
        if user.role == Role.PARENT and self.students.is_guardian(
            guardian_id=user.id, student_id=student.id
        ):
            return
        raise self._forbidden()

    def ensure_is_guardian(self, user: User, student: Student) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role == Role.PARENT and self.students.is_guardian(
            guardian_id=user.id, student_id=student.id
        ):
            return
        raise self._forbidden()

    def ensure_can_view_surveys(self, user: User, student: Student) -> None:
        """Socio-family data is restricted: teachers only see the resulting risk."""
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role in STAFF_WITH_FULL_ACCESS:
            return
        if user.role == Role.PARENT and self.students.is_guardian(
            guardian_id=user.id, student_id=student.id
        ):
            return
        raise self._forbidden()

    def ensure_can_manage_commitments(self, user: User, student: Student) -> None:
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role == Role.DIRECTOR:
            return
        if user.role == Role.TEACHER and student.classroom.tutor_id == user.id:
            return
        raise self._forbidden()

    def ensure_can_view_commitments(self, user: User, student: Student) -> None:
        """Meeting minutes are visible to the parties involved and the director."""
        self._ensure_same_institution(user, student.institution_id, "Student")
        if user.role == Role.DIRECTOR:
            return
        if user.role == Role.TEACHER and student.classroom.tutor_id == user.id:
            return
        if user.role == Role.PARENT and self.students.is_guardian(
            guardian_id=user.id, student_id=student.id
        ):
            return
        raise self._forbidden()

    def ensure_can_manage_situations(self, user: User, student: Student) -> None:
        """Context situations are sensitive: only the classroom tutor and the director."""
        self.ensure_can_manage_commitments(user, student)

    def ensure_can_manage_checkin(self, user: User, classroom: Classroom) -> None:
        self._ensure_same_institution(user, classroom.institution_id, "Classroom")
        if user.role == Role.DIRECTOR:
            return
        if user.role == Role.TEACHER and classroom.tutor_id == user.id:
            return
        raise self._forbidden()

    @staticmethod
    def _ensure_same_institution(user: User, institution_id: int, resource: str) -> None:
        # Records from other institutions are reported as missing, not forbidden,
        # so their existence is not disclosed.
        if user.institution_id != institution_id:
            raise NotFoundError(f"{resource} not found")

    @staticmethod
    def _forbidden() -> ForbiddenError:
        return ForbiddenError("You do not have access to this resource")
