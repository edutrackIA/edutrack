from pydantic import BaseModel, Field

from app.domain import User


class GuardianInput(BaseModel):
    full_name: str = Field(min_length=3, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    kinship: str = Field(default="Apoderado", max_length=30)


class GuardianResponse(BaseModel):
    id: int
    full_name: str
    email: str
    kinship: str
    has_access: bool
    # Only set right after an action that tried to email an invitation.
    invitation_sent: bool | None = None

    @classmethod
    def from_model(
        cls, user: User, kinship: str, *, invitation_sent: bool | None = None
    ) -> "GuardianResponse":
        return cls(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            kinship=kinship,
            has_access=user.has_access,
            invitation_sent=invitation_sent,
        )
