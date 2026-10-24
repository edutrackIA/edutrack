from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain import ParentEducation


class FamilySurveyInput(BaseModel):
    period_id: int
    study_hours_week: int = Field(ge=0, le=60)
    parent_education: ParentEducation
    home_internet: bool
    has_study_device: bool
    family_communication: int = Field(ge=1, le=5)
    student_works: bool
    household_size: int = Field(ge=1, le=20)


class FamilySurveyResponse(FamilySurveyInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    responder_id: int
    submitted_at: datetime
