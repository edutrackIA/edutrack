from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain import SituationKind, StudentSituation
from app.services.situations.catalog import SITUATIONS


class SituationKindInfo(BaseModel):
    kind: SituationKind
    label: str
    group: Literal["MESSAGE", "TEAM"]
    description: str


class SituationInput(BaseModel):
    kind: SituationKind
    note: str | None = Field(default=None, max_length=500)
    started_on: date | None = None


class SituationUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=500)
    resolved: bool | None = None


class SituationResponse(BaseModel):
    id: int
    student_id: int
    kind: SituationKind
    label: str
    group: Literal["MESSAGE", "TEAM"]
    note: str | None
    started_on: date
    resolved_on: date | None
    created_at: datetime

    @classmethod
    def from_model(cls, situation: StudentSituation) -> "SituationResponse":
        info = SITUATIONS[situation.kind]
        return cls(
            id=situation.id,
            student_id=situation.student_id,
            kind=situation.kind,
            label=info.label,
            group=info.group,
            note=situation.note,
            started_on=situation.started_on,
            resolved_on=situation.resolved_on,
            created_at=situation.created_at,
        )


class CheckinResponse(BaseModel):
    classroom_id: int
    week_start: date
    deadline: date
    editable: bool
    completed: bool
    completed_at: datetime | None
