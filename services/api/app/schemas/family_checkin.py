from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain import FamilyCheckin, FamilyMood, HomeChange
from app.schemas.student import StudentListItem

HOME_CHANGE_LABELS = {
    HomeChange.MOVING: "Mudanza",
    HomeChange.HEALTH: "Salud de algún familiar o del estudiante",
    HomeChange.PARENTS_WORK: "Cambios en el trabajo de los padres",
    HomeChange.CARING_FAMILY: "Cuidado de hermanos o familiares",
    HomeChange.ECONOMIC: "Dificultades económicas",
    HomeChange.OTHER: "Otro cambio",
}

MOOD_LABELS = {
    FamilyMood.GOOD: "Lo vemos bien",
    FamilyMood.OK: "Regular",
    FamilyMood.WORRIED: "Nos preocupa",
}


class FamilyCheckinInput(BaseModel):
    mood: FamilyMood
    home_changes: list[HomeChange] = Field(default_factory=list, max_length=6)
    peer_concern: bool = False
    comment: str | None = Field(default=None, max_length=500)


class FamilyCheckinResponse(BaseModel):
    id: int
    student: StudentListItem
    month: date
    mood: FamilyMood
    mood_label: str
    home_changes: list[HomeChange]
    home_change_labels: list[str]
    peer_concern: bool
    comment: str | None
    submitted_at: datetime
    reviewed_at: datetime | None

    @classmethod
    def from_model(cls, checkin: FamilyCheckin) -> "FamilyCheckinResponse":
        changes = [HomeChange(change) for change in checkin.home_changes]
        return cls(
            id=checkin.id,
            student=StudentListItem.from_model(checkin.student),
            month=checkin.month,
            mood=checkin.mood,
            mood_label=MOOD_LABELS[checkin.mood],
            home_changes=changes,
            home_change_labels=[HOME_CHANGE_LABELS[change] for change in changes],
            peer_concern=checkin.peer_concern,
            comment=checkin.comment,
            submitted_at=checkin.submitted_at,
            reviewed_at=checkin.reviewed_at,
        )


class CurrentFamilyCheckin(BaseModel):
    month: date
    checkin: FamilyCheckinResponse | None
