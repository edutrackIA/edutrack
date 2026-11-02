from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain import DataRequest, DataRequestKind, DataRequestStatus


class PrivacyStatus(BaseModel):
    version: str
    accepted_at: datetime | None


class ConsentInput(BaseModel):
    version: str


class DataRequestInput(BaseModel):
    student_id: int
    kind: DataRequestKind
    details: str = Field(min_length=10, max_length=2000)


class DataRequestResolution(BaseModel):
    status: DataRequestStatus
    response: str = Field(min_length=10, max_length=2000)


class DataRequestResponse(BaseModel):
    id: int
    student_id: int
    student_name: str
    requester_name: str
    kind: DataRequestKind
    details: str
    status: DataRequestStatus
    response: str | None
    created_at: datetime
    due_date: date
    resolved_at: datetime | None

    @classmethod
    def from_model(cls, request: DataRequest, due_date: date) -> "DataRequestResponse":
        return cls(
            id=request.id,
            student_id=request.student_id,
            student_name=request.student.full_name,
            requester_name=request.requester.full_name,
            kind=request.kind,
            details=request.details,
            status=request.status,
            response=request.response,
            created_at=request.created_at,
            due_date=due_date,
            resolved_at=request.resolved_at,
        )
