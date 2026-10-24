"""Create demo data for local development. Safe to run more than once."""

import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.domain import (
    AcademicPeriod,
    BehaviorRecord,
    Classroom,
    CourseAssignment,
    Grade,
    Guardianship,
    Institution,
    Role,
    Sex,
    Student,
    Subject,
    User,
)

DEMO_PASSWORD = "Edutrack123!"
YEAR = 2026

DEMO_USERS = [
    ("director@edutrack.dev", "Carmen Rojas", Role.DIRECTOR),
    ("docente@edutrack.dev", "Luis Quispe", Role.TEACHER),
    ("docente2@edutrack.dev", "Ana Torres", Role.TEACHER),
    ("padre@edutrack.dev", "Rosa Huamán", Role.PARENT),
    ("analista@edutrack.dev", "Jorge Salazar", Role.ANALYST),
]

SUBJECTS = [
    "Matemática",
    "Comunicación",
    "Ciencia y Tecnología",
    "Ciencias Sociales",
    "Inglés",
    "Educación Física",
]

BIMESTERS = [
    (1, date(YEAR, 3, 9), date(YEAR, 5, 8)),
    (2, date(YEAR, 5, 18), date(YEAR, 7, 17)),
    (3, date(YEAR, 8, 3), date(YEAR, 10, 2)),
    (4, date(YEAR, 10, 12), date(YEAR, 12, 18)),
]

# fmt: off
FIRST_NAMES = [
    ("Mateo", Sex.M), ("Valentina", Sex.F), ("Santiago", Sex.M), ("Camila", Sex.F),
    ("Diego", Sex.M), ("Lucía", Sex.F), ("Sebastián", Sex.M), ("Daniela", Sex.F),
    ("Adrián", Sex.M), ("Fernanda", Sex.F), ("Gabriel", Sex.M), ("Mariana", Sex.F),
]

LAST_NAMES = [
    "Flores", "García", "Mendoza", "Ramírez", "Castillo", "Chávez",
    "Vargas", "Paredes", "Gutiérrez", "Rojas", "Salas", "Córdova",
]
# fmt: on


def get_or_create_institution(db: Session) -> Institution:
    institution = db.scalar(select(Institution).order_by(Institution.id))
    if institution is None:
        institution = Institution(name="I.E.P. Demo EduTrack", ugel="UGEL 03", district="Lince")
        db.add(institution)
        db.flush()
    return institution


def ensure_users(db: Session, institution: Institution) -> dict[str, User]:
    users: dict[str, User] = {}
    password_hash = hash_password(DEMO_PASSWORD)
    for email, full_name, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                institution_id=institution.id,
                email=email,
                full_name=full_name,
                role=role,
                password_hash=password_hash,
            )
            db.add(user)
            db.flush()
        users[email] = user
    return users


def ensure_academic_data(db: Session, institution: Institution, users: dict[str, User]) -> bool:
    if db.scalar(select(Classroom.id).where(Classroom.institution_id == institution.id)):
        return False

    rng = random.Random(42)

    periods = [
        AcademicPeriod(
            institution_id=institution.id, year=YEAR, bimester=n, start_date=start, end_date=end
        )
        for n, start, end in BIMESTERS
    ]
    subjects = [
        db.scalar(select(Subject).where(Subject.name == name)) or Subject(name=name)
        for name in SUBJECTS
    ]
    db.add_all(periods + subjects)
    db.flush()

    teacher = users["docente@edutrack.dev"]
    teacher_2 = users["docente2@edutrack.dev"]
    classroom_a = Classroom(
        institution_id=institution.id, tutor_id=teacher.id, year=YEAR, grade=3, section="A"
    )
    classroom_b = Classroom(
        institution_id=institution.id, tutor_id=teacher_2.id, year=YEAR, grade=3, section="B"
    )
    db.add_all([classroom_a, classroom_b])
    db.flush()

    for classroom, owner in ((classroom_a, teacher), (classroom_b, teacher_2)):
        db.add_all(
            CourseAssignment(classroom_id=classroom.id, subject_id=subject.id, teacher_id=owner.id)
            for subject in subjects
        )

    students: list[Student] = []
    for index in range(20):
        first_name, sex = FIRST_NAMES[index % len(FIRST_NAMES)]
        classroom = classroom_a if index < 10 else classroom_b
        students.append(
            Student(
                institution_id=institution.id,
                classroom_id=classroom.id,
                code=f"{YEAR}{index + 1:04d}",
                first_name=first_name,
                last_name=f"{rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}",
                birth_date=date(YEAR - 14, rng.randint(1, 12), rng.randint(1, 28)),
                sex=sex,
            )
        )
    db.add_all(students)
    db.flush()

    db.add(
        Guardianship(
            guardian_id=users["padre@edutrack.dev"].id, student_id=students[0].id, kinship="Madre"
        )
    )

    for student in students:
        base = rng.uniform(9, 18)
        for period in periods[:3]:
            for subject in subjects:
                score = min(20.0, max(0.0, rng.gauss(base, 2)))
                db.add(
                    Grade(
                        student_id=student.id,
                        subject_id=subject.id,
                        period_id=period.id,
                        score=round(score, 1),
                    )
                )
            db.add(
                BehaviorRecord(student_id=student.id, period_id=period.id, rating=rng.randint(2, 5))
            )
    return True


def main() -> None:
    with SessionLocal() as db:
        institution = get_or_create_institution(db)
        users = ensure_users(db, institution)
        created = ensure_academic_data(db, institution, users)
        db.commit()

    print(f"Demo users ready ({len(DEMO_USERS)}), password {DEMO_PASSWORD!r}.")
    print("Academic data created." if created else "Academic data already exists.")


if __name__ == "__main__":
    main()
