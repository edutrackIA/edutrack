"""Create demo data for local development. Safe to run more than once."""

import random
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.domain import (
    AcademicPeriod,
    Attendance,
    AttendanceStatus,
    BehaviorRecord,
    Classroom,
    Commitment,
    CourseAssignment,
    FamilySurvey,
    Grade,
    Guardianship,
    Institution,
    ParentEducation,
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


def ensure_attendance(db: Session, institution: Institution) -> bool:
    exists = db.scalar(
        select(Attendance.id)
        .join(Student, Student.id == Attendance.student_id)
        .where(Student.institution_id == institution.id)
        .limit(1)
    )
    if exists:
        return False

    students = db.scalars(select(Student).where(Student.institution_id == institution.id)).all()
    periods = db.scalars(
        select(AcademicPeriod)
        .where(AcademicPeriod.institution_id == institution.id, AcademicPeriod.bimester <= 3)
        .order_by(AcademicPeriod.bimester)
    ).all()
    school_days = [
        period.start_date + timedelta(days=offset)
        for period in periods
        for offset in range((period.end_date - period.start_date).days + 1)
        if (period.start_date + timedelta(days=offset)).weekday() < 5
    ]

    rng = random.Random(7)
    statuses = [
        AttendanceStatus.PRESENT,
        AttendanceStatus.ABSENT,
        AttendanceStatus.LATE,
        AttendanceStatus.JUSTIFIED,
    ]
    for student in students:
        absence_rate = rng.choice([0.02, 0.04, 0.06, 0.12, 0.2])
        weights = [1 - absence_rate * 1.5, absence_rate, absence_rate * 0.3, absence_rate * 0.2]
        db.add_all(
            Attendance(student_id=student.id, date=day, status=rng.choices(statuses, weights)[0])
            for day in school_days
        )
    return True


def ensure_surveys(db: Session, institution: Institution, users: dict[str, User]) -> bool:
    students = db.scalars(
        select(Student).where(Student.institution_id == institution.id).order_by(Student.code)
    ).all()
    first_period = db.scalar(
        select(AcademicPeriod).where(
            AcademicPeriod.institution_id == institution.id, AcademicPeriod.bimester == 1
        )
    )
    if not students or first_period is None:
        return False
    if db.scalar(select(FamilySurvey.id).where(FamilySurvey.student_id == students[0].id)):
        return False

    rng = random.Random(11)
    parent = users["padre@edutrack.dev"]
    analyst = users["analista@edutrack.dev"]
    for index, student in enumerate(students):
        db.add(
            FamilySurvey(
                student_id=student.id,
                period_id=first_period.id,
                responder_id=parent.id if index == 0 else analyst.id,
                study_hours_week=rng.randint(2, 20),
                parent_education=rng.choice(list(ParentEducation)),
                home_internet=rng.random() < 0.8,
                has_study_device=rng.random() < 0.75,
                family_communication=rng.randint(1, 5),
                student_works=rng.random() < 0.1,
                household_size=rng.randint(2, 8),
            )
        )
    return True


def ensure_commitments(db: Session, users: dict[str, User]) -> bool:
    parent = users["padre@edutrack.dev"]
    child = db.scalar(
        select(Student)
        .join(Guardianship, Guardianship.student_id == Student.id)
        .where(Guardianship.guardian_id == parent.id)
    )
    if child is None or db.scalar(select(Commitment.id).where(Commitment.student_id == child.id)):
        return False

    db.add(
        Commitment(
            student_id=child.id,
            tutor_id=child.classroom.tutor_id or users["docente@edutrack.dev"].id,
            guardian_id=parent.id,
            meeting_date=date(YEAR, 6, 12),
            agreements=(
                "La familia supervisará 1 hora diaria de estudio y revisará la agenda. "
                "El tutor enviará un reporte quincenal de avance en Matemática."
            ),
            follow_up_date=date(YEAR, 7, 10),
        )
    )
    return True


def main() -> None:
    with SessionLocal() as db:
        institution = get_or_create_institution(db)
        users = ensure_users(db, institution)
        created = ensure_academic_data(db, institution, users)
        db.flush()
        attendance_created = ensure_attendance(db, institution)
        surveys_created = ensure_surveys(db, institution, users)
        commitments_created = ensure_commitments(db, users)
        db.commit()

    print(f"Demo users ready ({len(DEMO_USERS)}), password {DEMO_PASSWORD!r}.")
    print("Academic data created." if created else "Academic data already exists.")
    print("Attendance created." if attendance_created else "Attendance already exists.")
    print("Surveys created." if surveys_created else "Surveys already exist.")
    print("Commitments created." if commitments_created else "Commitments already exist.")


if __name__ == "__main__":
    main()
