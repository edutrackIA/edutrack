import pytest

from app.api.deps import require_roles
from app.core.errors import ForbiddenError
from app.domain import Role, User


def build_user(role: Role) -> User:
    return User(id=1, institution_id=1, email="u@test.dev", full_name="U", role=role)


def test_require_roles_allows_listed_role() -> None:
    checker = require_roles(Role.DIRECTOR, Role.ANALYST)
    user = build_user(Role.ANALYST)

    assert checker(user) is user


def test_require_roles_rejects_other_roles() -> None:
    checker = require_roles(Role.DIRECTOR)

    with pytest.raises(ForbiddenError):
        checker(build_user(Role.PARENT))
