"""Enrollment over time: withdrawals, transfers, graduation and moving up a grade."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.domain import (
    Classroom,
    ExitReason,
    Recommendation,
    RecommendationStatus,
    Student,
    StudentStatus,
    User,
)
from app.repositories.student_repository import StudentRepository
from app.schemas.student import PromotionInput, PromotionMove, PromotionPlan, WithdrawalInput
from app.services.access_policy import AccessPolicy


def _invalid(message: str) -> UnprocessableError:
    return UnprocessableError(message, code="ENROLLMENT_INVALID")


class EnrollmentService:
    def __init__(self, db: Session, today: date) -> None:
        self.db = db
        self.today = today
        self.students = StudentRepository(db)
        self.policy = AccessPolicy(db)

    # --- Retiros y traslados ---------------------------------------------------------------

    def withdraw(self, user: User, student_id: int, data: WithdrawalInput) -> Student:
        student = self._student(user, student_id)
        if not student.is_enrolled:
            raise ConflictError("El estudiante ya no está matriculado", code="NOT_ENROLLED")
        if data.reason == ExitReason.GRADUATION:
            raise _invalid("El egreso se registra con el cierre del año")
        if data.exit_date > self.today:
            raise _invalid("La fecha de salida no puede ser futura")

        student.status = (
            StudentStatus.TRANSFERRED
            if data.reason == ExitReason.TRANSFER
            else StudentStatus.WITHDRAWN
        )
        student.exit_date = data.exit_date
        student.exit_reason = data.reason
        student.exit_note = (data.note or "").strip() or None
        # Pending suggestions no longer reach anyone: clear them from the tutor's queue.
        for recommendation in self.db.scalars(
            select(Recommendation).where(
                Recommendation.student_id == student.id,
                Recommendation.status == RecommendationStatus.PENDING_REVIEW,
            )
        ):
            recommendation.status = RecommendationStatus.DISCARDED
        self.db.commit()
        return student

    def reinstate(self, user: User, student_id: int) -> Student:
        """Undo a withdrawal registered by mistake, or a student who came back."""
        student = self._student(user, student_id)
        if student.is_enrolled:
            raise ConflictError("El estudiante ya está matriculado", code="ALREADY_ENROLLED")
        student.status = StudentStatus.ENROLLED
        student.exit_date = student.exit_reason = student.exit_note = None
        self.db.commit()
        return student

    # --- Cierre del año -------------------------------------------------------------------

    def promote(self, user: User, year: int, data: PromotionInput) -> PromotionPlan:
        """Move every enrolled student of `year` to `year + 1`.

        Repeaters stay in the same grade; students in the final grade graduate. Classrooms
        for the next year are created as needed (same section, without tutor).
        """
        repeating = {code.strip() for code in data.repeating_codes if code.strip()}
        classrooms = self.db.scalars(
            select(Classroom)
            .where(Classroom.institution_id == user.institution_id, Classroom.year == year)
            .order_by(Classroom.grade, Classroom.section)
        ).all()
        if not classrooms:
            raise _invalid(f"No hay aulas registradas en {year}")

        known: set[str] = set()
        moves: dict[tuple[str, str], int] = {}
        counts = {"promoted": 0, "repeating": 0, "graduated": 0}
        targets: dict[tuple[int, str], Classroom] = {}

        for classroom in classrooms:
            # Asked to the database, not read from classroom.students: a collection loaded
            # earlier in the session would still list students already moved out.
            enrolled = self.db.scalars(
                select(Student)
                .where(
                    Student.classroom_id == classroom.id,
                    Student.status == StudentStatus.ENROLLED,
                )
                .order_by(Student.id)
            ).all()
            for student in enrolled:
                known.add(student.code)
                source = f"{classroom.label} ({year})"
                if student.code in repeating:
                    grade, kind = classroom.grade, "repeating"
                elif classroom.grade >= data.final_grade:
                    moves[(source, "Egresan")] = moves.get((source, "Egresan"), 0) + 1
                    counts["graduated"] += 1
                    if not data.dry_run:
                        student.status = StudentStatus.GRADUATED
                        student.exit_date = self.today
                        student.exit_reason = ExitReason.GRADUATION
                    continue
                else:
                    grade, kind = classroom.grade + 1, "promoted"

                target_label = f"{grade}° {classroom.section} ({year + 1})"
                moves[(source, target_label)] = moves.get((source, target_label), 0) + 1
                counts[kind] += 1
                if not data.dry_run:
                    target = targets.get((grade, classroom.section)) or self._next_classroom(
                        user, year + 1, grade, classroom.section
                    )
                    targets[(grade, classroom.section)] = target
                    student.classroom_id = target.id

        if not data.dry_run:
            self.db.commit()
        return PromotionPlan(
            year=year,
            moves=[
                PromotionMove(source=source, target=target, students=count)
                for (source, target), count in moves.items()
            ],
            promoted=counts["promoted"],
            repeating=counts["repeating"],
            graduated=counts["graduated"],
            unknown_codes=sorted(repeating - known),
            applied=not data.dry_run,
        )

    # --- Internos ------------------------------------------------------------------------

    def _next_classroom(self, user: User, year: int, grade: int, section: str) -> Classroom:
        existing = self.db.scalar(
            select(Classroom).where(
                Classroom.institution_id == user.institution_id,
                Classroom.year == year,
                Classroom.grade == grade,
                Classroom.section == section,
            )
        )
        if existing is not None:
            return existing
        classroom = Classroom(
            institution_id=user.institution_id, year=year, grade=grade, section=section
        )
        self.db.add(classroom)
        self.db.flush()
        return classroom

    def _student(self, user: User, student_id: int) -> Student:
        student = self.students.get(student_id)
        if student is None:
            raise NotFoundError("Student not found")
        self.policy.ensure_can_manage_enrollment(user, student)
        return student
