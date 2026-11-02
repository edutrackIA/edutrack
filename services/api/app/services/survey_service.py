from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.domain import FamilySurvey, Student, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.survey_repository import SurveyRepository
from app.schemas.survey import FamilySurveyInput
from app.services.access_policy import AccessPolicy
from app.services.privacy_service import PrivacyService


class SurveyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.surveys = SurveyRepository(db)
        self.students = StudentRepository(db)
        self.academic = AcademicRepository(db)
        self.policy = AccessPolicy(db)

    def submit(self, user: User, student_id: int, data: FamilySurveyInput) -> FamilySurvey:
        PrivacyService(self.db).ensure_consent(user)
        student = self._get_student(student_id)
        self.policy.ensure_can_submit_survey(user, student)

        period = self.academic.get_period(data.period_id)
        if period is None or period.institution_id != user.institution_id:
            raise UnprocessableError(f"Invalid period {data.period_id}")
        if self.surveys.get_for_period(student_id=student.id, period_id=period.id):
            raise ConflictError("A survey was already submitted for this period")

        survey = self.surveys.add(
            FamilySurvey(student_id=student.id, responder_id=user.id, **data.model_dump())
        )
        self.db.commit()
        return survey

    def list_for_student(self, user: User, student_id: int) -> list[FamilySurvey]:
        student = self._get_student(student_id)
        self.policy.ensure_can_view_surveys(user, student)
        return self.surveys.list_for_student(student.id)

    def _get_student(self, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        return student
