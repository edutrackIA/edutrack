"""Create a demo institution and one user per role for local development."""

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.domain import Institution, Role, User
from app.repositories.user_repository import UserRepository

DEMO_PASSWORD = "Edutrack123!"

DEMO_USERS = [
    ("director@edutrack.dev", "Carmen Rojas", Role.DIRECTOR),
    ("docente@edutrack.dev", "Luis Quispe", Role.TEACHER),
    ("padre@edutrack.dev", "Rosa Huamán", Role.PARENT),
    ("analista@edutrack.dev", "Jorge Salazar", Role.ANALYST),
]


def main() -> None:
    with SessionLocal() as db:
        users = UserRepository(db)
        if users.get_by_email(DEMO_USERS[0][0]) is not None:
            print("Demo data already exists.")
            return

        institution = Institution(name="I.E.P. Demo EduTrack", ugel="UGEL 03", district="Lince")
        db.add(institution)
        db.flush()

        password_hash = hash_password(DEMO_PASSWORD)
        for email, full_name, role in DEMO_USERS:
            users.add(
                User(
                    institution_id=institution.id,
                    email=email,
                    full_name=full_name,
                    role=role,
                    password_hash=password_hash,
                )
            )
        db.commit()

    print(f"Created {len(DEMO_USERS)} demo users with password {DEMO_PASSWORD!r}.")


if __name__ == "__main__":
    main()
