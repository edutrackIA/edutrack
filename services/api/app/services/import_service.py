from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import (
    NotFoundError,
    PayloadTooLargeError,
    UnprocessableError,
    UnsupportedMediaTypeError,
)
from app.domain import ImportJob, ImportKind, ImportStatus, User
from app.repositories.academic_repository import AcademicRepository
from app.repositories.import_repository import ImportRepository
from app.services.imports.importers import (
    AttendanceImporter,
    GradeImporter,
    GuardianImporter,
    RowImporter,
    RowValidationError,
    StudentImporter,
)
from app.services.imports.parsing import FileFormatError, UnsupportedFileError, parse_file
from app.services.invitation_service import InvitationService
from app.services.notifications.email_sender import EmailSender

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000
MAX_STORED_ERRORS = 200

TEMPLATES = {
    ImportKind.STUDENTS: (
        "code,first_name,last_name,birth_date,sex,year,grade,section\n"
        "20260101,Ana,Pérez Soto,2012-04-15,F,2026,3,A\n"
    ),
    ImportKind.GRADES: "student_code,subject,score\n20260001,Matemática,15.5\n",
    ImportKind.ATTENDANCE: "student_code,date,status\n20260001,2026-03-10,PRESENT\n",
    ImportKind.GUARDIANS: (
        "student_code,full_name,email,kinship\n"
        "20260001,Rosa Huamán Flores,rosa.huaman@correo.com,Madre\n"
    ),
}


class ImportService:
    def __init__(self, db: Session, sender: EmailSender | None = None) -> None:
        self.db = db
        self.sender = sender
        self.jobs = ImportRepository(db)
        self.academic = AcademicRepository(db)
        self.dry_run = False

    def run(
        self,
        user: User,
        *,
        kind: ImportKind,
        filename: str,
        content: bytes,
        period_id: int | None = None,
        dry_run: bool = False,
    ) -> ImportJob:
        """Import the valid rows. With dry_run, validate everything and save nothing."""
        self.dry_run = dry_run
        if len(content) > MAX_UPLOAD_BYTES:
            raise PayloadTooLargeError(f"Files are limited to {MAX_UPLOAD_BYTES // 1024} KB")
        importer = self._importer(user, kind, period_id)

        job = ImportJob(
            institution_id=user.institution_id,
            uploaded_by=user.id,
            kind=kind,
            filename=filename[:255],
            status=ImportStatus.PENDING,
            rows_ok=0,
            rows_failed=0,
            errors=[],
        )

        try:
            headers, rows = parse_file(filename, content)
        except UnsupportedFileError as exc:
            raise UnsupportedMediaTypeError("Only .csv and .xlsx files are supported") from exc
        except FileFormatError as exc:
            return self._finish(job, [_error(None, None, str(exc))])

        missing = [column for column in importer.required_columns if column not in headers]
        if missing:
            errors = [_error(1, column, "Falta la columna") for column in missing]
            return self._finish(job, errors)
        if not rows:
            return self._finish(job, [_error(None, None, "El archivo no tiene filas con datos")])
        if len(rows) > MAX_ROWS:
            return self._finish(
                job, [_error(None, None, f"El archivo supera el máximo de {MAX_ROWS} filas")]
            )

        errors: list[dict[str, Any]] = []
        first_line: dict[object, int] = {}
        for line_number, row in rows:
            key = importer.key(row)
            if key in first_line:
                message = f"Fila repetida: ya aparece en la fila {first_line[key]}"
                errors.append(_error(line_number, None, message))
                continue
            first_line[key] = line_number
            try:
                importer.import_row(row)
                job.rows_ok += 1
            except RowValidationError as exc:
                errors.append(_error(line_number, exc.column, exc.message))

        job = self._finish(job, errors)
        if not self.dry_run:
            importer.after_commit()
        return job

    def get(self, user: User, job_id: int) -> ImportJob:
        job = self.jobs.get(job_id)
        if job is None or job.institution_id != user.institution_id:
            raise NotFoundError("Import not found")
        return job

    def _importer(self, user: User, kind: ImportKind, period_id: int | None) -> RowImporter:
        if kind == ImportKind.STUDENTS:
            return StudentImporter(self.db, user.institution_id)
        if kind == ImportKind.ATTENDANCE:
            return AttendanceImporter(self.db, user.institution_id)
        if kind == ImportKind.GUARDIANS:
            invitations = InvitationService(self.db, self.sender)
            return GuardianImporter(self.db, user.institution_id, invitations.invite)

        if period_id is None:
            raise UnprocessableError("period_id is required for grade imports")
        period = self.academic.get_period(period_id)
        if period is None or period.institution_id != user.institution_id:
            raise UnprocessableError(f"Invalid period {period_id}")
        return GradeImporter(self.db, user.institution_id, period_id)

    def _finish(self, job: ImportJob, errors: list[dict[str, Any]]) -> ImportJob:
        row_errors = {error["row"] for error in errors if error["row"] and error["row"] > 1}
        job.rows_failed = len(row_errors)
        job.errors = errors[:MAX_STORED_ERRORS]
        job.status = ImportStatus.DONE if job.rows_ok > 0 else ImportStatus.FAILED
        if self.dry_run:
            # Preview: undo every row written while validating, keep only the report.
            self.db.rollback()
            return job
        self.jobs.add(job)
        self.db.commit()
        return job


def _error(row: int | None, column: str | None, message: str) -> dict[str, Any]:
    return {"row": row, "column": column, "message": message}
