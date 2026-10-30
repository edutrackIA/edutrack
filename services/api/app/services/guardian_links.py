"""Shared rules to register a guardian, used by the form and by the import."""

from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email
from sqlalchemy.orm import Session

from app.domain import Guardianship, Role, Student, User
from app.repositories.user_repository import UserRepository


class GuardianLinkError(Exception):
    def __init__(self, column: str, message: str, *, invalid_input: bool = False) -> None:
        super().__init__(message)
        self.column = column
        self.message = message
        # True for malformed data (422); False for a clash with existing accounts (409).
        self.invalid_input = invalid_input


@dataclass
class GuardianLink:
    user: User
    created_user: bool


def normalize_email(raw: str) -> str:
    try:
        return validate_email(raw.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise GuardianLinkError(
            "email", f"{raw} no es un correo válido", invalid_input=True
        ) from exc


def link_guardian(
    db: Session, student: Student, *, full_name: str, email: str, kinship: str
) -> GuardianLink:
    """Find the parent account by email (or create it without password) and link it.

    One guardian can have several children, so an existing PARENT account is reused.
    """
    full_name = " ".join(full_name.split())
    kinship = kinship.strip() or "Apoderado"
    if len(full_name) < 3:
        raise GuardianLinkError("full_name", "Falta el nombre del apoderado", invalid_input=True)
    email = normalize_email(email)

    users = UserRepository(db)
    user = users.get_by_email(email)
    created = False
    if user is None:
        user = User(
            institution_id=student.institution_id,
            email=email,
            password_hash=None,
            full_name=full_name,
            role=Role.PARENT,
        )
        db.add(user)
        db.flush()
        created = True
    elif user.role != Role.PARENT or user.institution_id != student.institution_id:
        raise GuardianLinkError("email", f"El correo {email} ya pertenece a otro usuario")

    link = db.get(Guardianship, (user.id, student.id))
    if link is None:
        db.add(Guardianship(guardian_id=user.id, student_id=student.id, kinship=kinship[:30]))
    else:
        link.kinship = kinship[:30]
    db.flush()
    return GuardianLink(user=user, created_user=created)
