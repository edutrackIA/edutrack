from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain import CommitmentStatus


class CommitmentInput(BaseModel):
    guardian_id: int
    meeting_date: date
    agreements: str = Field(min_length=1, max_length=4000)
    follow_up_date: date | None = None

    @model_validator(mode="after")
    def follow_up_after_meeting(self) -> Self:
        if self.follow_up_date is not None and self.follow_up_date < self.meeting_date:
            raise ValueError("follow_up_date must be on or after meeting_date")
        return self


class CommitmentUpdate(BaseModel):
    agreements: str | None = Field(default=None, min_length=1, max_length=4000)
    follow_up_date: date | None = None
    status: CommitmentStatus | None = None


class CommitmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    tutor_id: int
    guardian_id: int
    meeting_date: date
    agreements: str
    follow_up_date: date | None
    status: CommitmentStatus
    created_at: datetime
