import os

os.environ["API_BCRYPT_ROUNDS"] = "4"
os.environ["API_JWT_SECRET"] = "test-secret-key-that-is-at-least-32-bytes-long"

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.domain import Institution, Role, User  # noqa: E402
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
