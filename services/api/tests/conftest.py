import os

os.environ["API_BCRYPT_ROUNDS"] = "4"
os.environ["API_JWT_SECRET"] = "test-secret-key-that-is-at-least-32-bytes-long"

from collections.abc import Callable, Iterator  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import date, timedelta  # noqa: E402
from email.message import EmailMessage  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.privacy import PRIVACY_NOTICE_VERSION  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.domain import (  # noqa: E402
    AcademicPeriod,
    Attendance,
    AttendanceStatus,
    Classroom,
    CourseAssignment,
    FamilySurvey,
    Grade,
    Guardianship,
    Institution,
    ParentEducation,
    PrivacyConsent,  # noqa: E402
    Role,
    Sex,
    Student,
    Subject,
    User,
)
from app.main import app  # noqa: E402
from app.services.notifications.email_sender import get_email_sender  # noqa: E402
from app.services.risk.ml_client import get_ml_client  # noqa: E402

DEFAULT_PASSWORD = "Secret123!"

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db_session() -> Iterator[Session]:
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def institution(db_session: Session) -> Institution:
    institution = Institution(name="I.E.P. Test", ugel="UGEL 03", district="Lince")
    db_session.add(institution)
    db_session.commit()
    return institution


@pytest.fixture
def make_user(db_session: Session, institution: Institution) -> Callable[..., User]:
    def factory(
        email: str = "director@test.dev",
        role: Role = Role.DIRECTOR,
        password: str = DEFAULT_PASSWORD,
        is_active: bool = True,
    ) -> User:
        user = User(
            institution_id=institution.id,
            email=email,
            full_name="Test User",
            role=role,
            password_hash=hash_password(password),
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        return user

    return factory


@pytest.fixture
def login(client: TestClient) -> Callable[..., dict]:
    def do_login(email: str = "director@test.dev", password: str = DEFAULT_PASSWORD) -> dict:
        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()

    return do_login


@dataclass
class School:
    director: User
    analyst: User
    teacher: User
    other_teacher: User
    parent: User
    classroom_a: Classroom
    classroom_b: Classroom
    math: Subject
    language: Subject
    period: AcademicPeriod
    student_a: Student
    student_a2: Student
    student_b: Student
    foreign_student: Student
    foreign_classroom: Classroom
    foreign_period: AcademicPeriod


def _user(db: Session, institution_id: int, email: str, role: Role) -> User:
    user = User(
        institution_id=institution_id,
        email=email,
        full_name=email.split("@")[0].title(),
        role=role,
        password_hash=hash_password(DEFAULT_PASSWORD),
    )
    db.add(user)
    db.flush()
    return user


def _student(db: Session, classroom: Classroom, code: str, first: str, last: str) -> Student:
    student = Student(
        institution_id=classroom.institution_id,
        classroom_id=classroom.id,
        code=code,
        first_name=first,
        last_name=last,
        birth_date=date(2012, 5, 10),
        sex=Sex.F,
    )
    db.add(student)
    db.flush()
    return student


@pytest.fixture
def school(db_session: Session, institution: Institution) -> School:
    db = db_session
    other = Institution(name="Other School", ugel="UGEL 01", district="Comas")
    db.add(other)
    db.flush()

    director = _user(db, institution.id, "director@school.dev", Role.DIRECTOR)
    analyst = _user(db, institution.id, "analyst@school.dev", Role.ANALYST)
    teacher = _user(db, institution.id, "teacher@school.dev", Role.TEACHER)
    other_teacher = _user(db, institution.id, "teacher2@school.dev", Role.TEACHER)
    parent = _user(db, institution.id, "parent@school.dev", Role.PARENT)
    # The demo guardian already accepted the privacy notice; tests of consent create others.
    db.add(PrivacyConsent(user_id=parent.id, notice_version=PRIVACY_NOTICE_VERSION))

    math = Subject(institution_id=institution.id, name="Matemática")
    language = Subject(institution_id=institution.id, name="Comunicación")
    period = AcademicPeriod(
        institution_id=institution.id,
        year=2026,
        bimester=1,
        start_date=date(2026, 3, 9),
        end_date=date(2026, 5, 8),
    )
    foreign_period = AcademicPeriod(
        institution_id=other.id,
        year=2026,
        bimester=1,
        start_date=date(2026, 3, 9),
        end_date=date(2026, 5, 8),
    )
    db.add_all([math, language, period, foreign_period])
    db.flush()

    classroom_a = Classroom(
        institution_id=institution.id, tutor_id=teacher.id, year=2026, grade=3, section="A"
    )
    classroom_b = Classroom(
        institution_id=institution.id, tutor_id=other_teacher.id, year=2026, grade=3, section="B"
    )
    foreign_classroom = Classroom(institution_id=other.id, year=2026, grade=3, section="A")
    db.add_all([classroom_a, classroom_b, foreign_classroom])
    db.flush()

    db.add(CourseAssignment(classroom_id=classroom_a.id, subject_id=math.id, teacher_id=teacher.id))
    db.add(
        CourseAssignment(classroom_id=classroom_b.id, subject_id=language.id, teacher_id=teacher.id)
    )

    student_a = _student(db, classroom_a, "A001", "Lucía", "Flores")
    student_a2 = _student(db, classroom_a, "A002", "Mateo", "Castillo")
    student_b = _student(db, classroom_b, "B001", "Diego", "Vargas")
    foreign_student = _student(db, foreign_classroom, "X001", "Ana", "Salas")
    db.add(Guardianship(guardian_id=parent.id, student_id=student_a.id, kinship="Madre"))
    db.commit()

    return School(
        director=director,
        analyst=analyst,
        teacher=teacher,
        other_teacher=other_teacher,
        parent=parent,
        classroom_a=classroom_a,
        classroom_b=classroom_b,
        math=math,
        language=language,
        period=period,
        student_a=student_a,
        student_a2=student_a2,
        student_b=student_b,
        foreign_student=foreign_student,
        foreign_classroom=foreign_classroom,
        foreign_period=foreign_period,
    )


def auth(user: User) -> dict[str, str]:
    token = create_access_token(
        user_id=user.id, role=user.role.value, institution_id=user.institution_id
    )
    return {"Authorization": f"Bearer {token}"}


# --- Riesgo ----------------------------------------------------------------


class FakeMlClient:
    """Deterministic stand-in for the ML service: lower averages mean higher risk."""

    version = "rf-test"

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []

    def predict_batch(self, items: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        self.calls.append(items)
        predictions = []
        for item in items:
            average = item["features"]["avg_score"]
            probability = round(max(0.0, min(1.0, (16 - average) / 8)), 4)
            predictions.append(
                {
                    "student_id": item["student_id"],
                    "probability": probability,
                    "model_version": self.version,
                    "top_factors": [
                        {"feature": "avg_score", "value": average, "contribution": 0.3}
                    ],
                }
            )
        return self.version, predictions


@pytest.fixture
def fake_ml() -> Iterator[FakeMlClient]:
    fake = FakeMlClient()
    app.dependency_overrides[get_ml_client] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_ml_client, None)


def add_records(
    db: Session,
    school: School,
    student: Student,
    scores: list[float],
    *,
    absences: int = 0,
    lates: int = 0,
    survey: bool = True,
    period: AcademicPeriod | None = None,
) -> None:
    period = period or school.period
    subjects = [school.math, school.language]
    for subject, score in zip(subjects, scores, strict=False):
        db.add(
            Grade(student_id=student.id, subject_id=subject.id, period_id=period.id, score=score)
        )
    statuses = (
        [AttendanceStatus.ABSENT] * absences
        + [AttendanceStatus.LATE] * lates
        + [AttendanceStatus.PRESENT] * (10 - absences - lates)
    )
    db.add_all(
        Attendance(student_id=student.id, date=period.start_date + timedelta(days=i), status=s)
        for i, s in enumerate(statuses)
    )
    if survey:
        db.add(
            FamilySurvey(
                student_id=student.id,
                period_id=period.id,
                responder_id=school.analyst.id,
                study_hours_week=6,
                parent_education=ParentEducation.SECONDARY,
                home_internet=True,
                has_study_device=False,
                family_communication=3,
                student_works=False,
                household_size=5,
            )
        )
    db.commit()


@pytest.fixture
def evaluated_school(school: School, db_session: Session) -> School:
    add_records(db_session, school, school.student_a, [8, 10], absences=3, lates=1)  # high
    add_records(db_session, school, school.student_a2, [17, 18])  # low
    add_records(db_session, school, school.student_b, [12, 13], survey=False)  # skipped
    return school


@pytest.fixture
def assessed_school(client: TestClient, evaluated_school: School, fake_ml: FakeMlClient) -> School:
    school = evaluated_school
    client.post(
        "/api/v1/risk-assessments/run",
        json={"period_id": school.period.id},
        headers=auth(school.analyst),
    )
    return school


# --- Correo ----------------------------------------------------------------


class Outbox:
    """Captures emails instead of sending them; can simulate an SMTP failure."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []
        self.fail = False

    def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise ConnectionRefusedError("SMTP server unavailable")
        self.messages.append(message)


@pytest.fixture(autouse=True)
def outbox() -> Iterator[Outbox]:
    box = Outbox()
    app.dependency_overrides[get_email_sender] = lambda: box
    yield box
    app.dependency_overrides.pop(get_email_sender, None)


@pytest.fixture(autouse=True)
def reset_rate_limits() -> Iterator[None]:
    """Failed-attempt counters live in memory; every test starts with a clean slate."""
    from app.core.rate_limit import ALL_LIMITERS

    for limiter in ALL_LIMITERS:
        limiter.clear()
    yield
