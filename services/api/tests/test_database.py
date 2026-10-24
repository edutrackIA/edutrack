from sqlalchemy.orm import Session

from app.core.database import get_db


def test_get_db_yields_a_session_and_closes_it() -> None:
    generator = get_db()
    session = next(generator)

    assert isinstance(session, Session)

    generator.close()
