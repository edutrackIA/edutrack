"""Create demo data for local development. Safe to run more than once.

    python -m scripts.seed_dev                 # demo school: 20 students in 3° A and 3° B
    python -m scripts.seed_dev --size large    # plus 18 classrooms of 30 (about 560 students)

Students follow coherent profiles (grades, attendance, conduct and family survey move
together), so the risk model yields the three levels instead of an all-green school.
"""

import argparse
import random
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import insert, select
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


@dataclass(frozen=True)
class Profile:
    """How a demo student does at school and at home."""

    score: tuple[float, float]
    absence: tuple[float, float]
    behavior: tuple[int, int]
    study_hours: tuple[int, int]
    internet: float
    device: float
    communication: tuple[int, int]
    works: float
    education: tuple[ParentEducation, ...]


HIGH = Profile(
    score=(7.5, 10.0),
    absence=(0.16, 0.24),
    behavior=(1, 2),
    study_hours=(1, 4),
    internet=0.2,
    device=0.2,
    communication=(1, 2),
    works=0.6,
    education=(ParentEducation.NONE, ParentEducation.PRIMARY),
)
MEDIUM = Profile(
    score=(10.0, 12.0),
    absence=(0.08, 0.13),
    behavior=(2, 3),
    study_hours=(4, 8),
    internet=0.6,
    device=0.6,
    communication=(2, 3),
    works=0.2,
    education=(ParentEducation.PRIMARY, ParentEducation.SECONDARY),
)
LOW = Profile(
    score=(13.0, 17.5),
    absence=(0.0, 0.04),
    behavior=(4, 5),
    study_hours=(8, 20),
    internet=0.95,
    device=0.9,
    communication=(4, 5),
    works=0.02,
    education=(ParentEducation.SECONDARY, ParentEducation.TECHNICAL, ParentEducation.UNIVERSITY),
)
# Out of every 20 students: 3 at high risk, 4 at moderate risk, the rest doing well.
HIGH_POSITIONS = {2, 7, 13}
MEDIUM_POSITIONS = {4, 9, 15, 18}

DEMO_CLASSROOMS = [(3, "A"), (3, "B")]
LARGE_CLASSROOMS = [
    (grade, section)
    for grade in range(1, 6)
    for section in "ABCD"
    if (grade, section) not in DEMO_CLASSROOMS
]
LARGE_CLASS_SIZE = 30


def profile_for(index: int) -> Profile:
    position = index % 20
    if position in HIGH_POSITIONS:
        return HIGH
    if position in MEDIUM_POSITIONS:
        return MEDIUM
    return LOW


def code_index(student: Student) -> int:
    """Demo codes are YEAR + a running number; the number decides the profile."""
    return int(student.code[-4:]) - 1


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
        db.scalar(
            select(Subject).where(Subject.institution_id == institution.id, Subject.name == name)
        )
        or Subject(institution_id=institution.id, name=name)
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

    students = create_students(db, institution, [classroom_a] * 10 + [classroom_b] * 10, 0, rng)

    db.add(
        Guardianship(
            guardian_id=users["padre@edutrack.dev"].id, student_id=students[0].id, kinship="Madre"
        )
    )
    add_grades(db, students, periods[:3], subjects, rng)
    return True


def create_students(
    db: Session,
    institution: Institution,
    classrooms: list[Classroom],
    first: int,
    rng: random.Random,
) -> list[Student]:
    students = []
    for offset, classroom in enumerate(classrooms):
        index = first + offset
        first_name, sex = FIRST_NAMES[index % len(FIRST_NAMES)]
        students.append(
            Student(
                institution_id=institution.id,
                classroom_id=classroom.id,
                code=f"{YEAR}{index + 1:04d}",
                first_name=first_name,
                last_name=f"{rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}",
                birth_date=date(
                    YEAR - 11 - classroom.grade, rng.randint(1, 12), rng.randint(1, 28)
                ),
                sex=sex,
            )
        )
    db.add_all(students)
    db.flush()
    return students


def add_grades(
    db: Session,
    students: list[Student],
    periods: list[AcademicPeriod],
    subjects: list[Subject],
    rng: random.Random,
) -> None:
    grades, behavior = [], []
    for student in students:
        profile = profile_for(code_index(student))
        base = rng.uniform(*profile.score)
        for period in periods:
            for subject in subjects:
                score = min(20.0, max(0.0, rng.gauss(base, 1.5)))
                grades.append(
                    {
                        "student_id": student.id,
                        "subject_id": subject.id,
                        "period_id": period.id,
                        "score": round(score, 1),
                    }
                )
            behavior.append(
                {
                    "student_id": student.id,
                    "period_id": period.id,
                    "rating": rng.randint(*profile.behavior),
                }
            )
    # Bulk inserts: the large school has tens of thousands of rows.
    db.execute(insert(Grade), grades)
    db.execute(insert(BehaviorRecord), behavior)


def ensure_large_school(db: Session, institution: Institution) -> int:
    """Extra classrooms to measure performance with a school of realistic size."""
    existing = {
        (classroom.grade, classroom.section)
        for classroom in db.scalars(
            select(Classroom).where(
                Classroom.institution_id == institution.id, Classroom.year == YEAR
            )
        )
    }
    missing = [key for key in LARGE_CLASSROOMS if key not in existing]
    if not missing:
        return 0
    rng = random.Random(99)
    classrooms = [
        Classroom(institution_id=institution.id, year=YEAR, grade=grade, section=section)
        for grade, section in missing
    ]
    db.add_all(classrooms)
    db.flush()
    count = len(
        db.scalars(select(Student.id).where(Student.institution_id == institution.id)).all()
    )
    seats = [classroom for classroom in classrooms for _ in range(LARGE_CLASS_SIZE)]
    students = create_students(db, institution, seats, count, rng)
    periods = db.scalars(
        select(AcademicPeriod)
        .where(AcademicPeriod.institution_id == institution.id, AcademicPeriod.bimester <= 3)
        .order_by(AcademicPeriod.bimester)
    ).all()
    subjects = db.scalars(select(Subject).where(Subject.institution_id == institution.id)).all()
    add_grades(db, students, list(periods), list(subjects), rng)
    return len(students)


def ensure_attendance(db: Session, institution: Institution) -> int:
    """Attendance for every school day of the first three periods, per student profile.

    Only students without any attendance yet get it, so new classrooms are filled too.
    """
    students = db.scalars(
        select(Student).where(Student.institution_id == institution.id).order_by(Student.code)
    ).all()
    with_attendance = set(db.scalars(select(Attendance.student_id).distinct()))
    pending = [student for student in students if student.id not in with_attendance]
    if not pending:
        return 0

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
    for student in pending:
        rate = rng.uniform(*profile_for(code_index(student)).absence)
        weights = [1 - rate * 1.5, rate, rate * 0.3, rate * 0.2]
        db.execute(
            insert(Attendance),
            [
                {"student_id": student.id, "date": day, "status": rng.choices(statuses, weights)[0]}
                for day in school_days
            ],
        )
    return len(pending)


def ensure_surveys(db: Session, institution: Institution, users: dict[str, User]) -> int:
    """First-period family survey for every student who has none, per profile."""
    students = db.scalars(
        select(Student).where(Student.institution_id == institution.id).order_by(Student.code)
    ).all()
    first_period = db.scalar(
        select(AcademicPeriod).where(
            AcademicPeriod.institution_id == institution.id, AcademicPeriod.bimester == 1
        )
    )
    if not students or first_period is None:
        return 0
    answered = set(db.scalars(select(FamilySurvey.student_id).distinct()))
    pending = [student for student in students if student.id not in answered]

    rng = random.Random(11)
    parent = users["padre@edutrack.dev"]
    analyst = users["analista@edutrack.dev"]
    for student in pending:
        index = code_index(student)
        profile = profile_for(index)
        db.add(
            FamilySurvey(
                student_id=student.id,
                period_id=first_period.id,
                responder_id=parent.id if index == 0 else analyst.id,
                study_hours_week=rng.randint(*profile.study_hours),
                parent_education=rng.choice(profile.education),
                home_internet=rng.random() < profile.internet,
                has_study_device=rng.random() < profile.device,
                family_communication=rng.randint(*profile.communication),
                student_works=rng.random() < profile.works,
                household_size=rng.randint(3, 8) if profile is HIGH else rng.randint(2, 6),
            )
        )
    return len(pending)


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--size",
        choices=["demo", "large"],
        default="demo",
        help="large adds about 560 students to measure performance",
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        institution = get_or_create_institution(db)
        users = ensure_users(db, institution)
        created = ensure_academic_data(db, institution, users)
        db.flush()
        extra = ensure_large_school(db, institution) if args.size == "large" else 0
        attendance = ensure_attendance(db, institution)
        surveys = ensure_surveys(db, institution, users)
        commitments_created = ensure_commitments(db, users)
        db.commit()

    print(f"Demo users ready ({len(DEMO_USERS)}), password {DEMO_PASSWORD!r}.")
    print("Academic data created." if created else "Academic data already exists.")
    if extra:
        print(f"Large school: {extra} students added.")
    print(f"Attendance added for {attendance} students; surveys for {surveys}.")
    print("Commitments created." if commitments_created else "Commitments already exist.")


if __name__ == "__main__":
    main()
