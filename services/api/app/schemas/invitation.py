from pydantic import BaseModel, Field


class InvitationInfo(BaseModel):
    """What the acceptance page shows: who is being invited."""

    full_name: str
    email: str


class AcceptInvitation(BaseModel):
    password: str = Field(min_length=1, max_length=128)
