import os

os.environ["API_BCRYPT_ROUNDS"] = "4"
os.environ["API_JWT_SECRET"] = "test-secret-key-that-is-at-least-32-bytes-long"

from collections.abc import Callable, Iterator  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.domain import (  # noqa: E402
    AcademicPeriod,
    Classroom,
    CourseAssignment,
    Guardianship,
    Institution,
    Role,
    Sex,
    Student,
    Subject,
    User,
)
from app.main import app  # noqa: E402

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

    math, language = Subject(name="Matemática"), Subject(name="Comunicación")
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
