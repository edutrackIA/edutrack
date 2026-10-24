from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.commitment import CommitmentInput, CommitmentResponse, CommitmentUpdate
from app.services.commitment_service import CommitmentService

router = APIRouter(prefix="/students/{student_id}/commitments", tags=["commitments"])


@router.get("", response_model=list[CommitmentResponse])
def list_commitments(student_id: int, user: CurrentUser, db: DbSession) -> list[CommitmentResponse]:
    commitments = CommitmentService(db).list_for_student(user, student_id)
    return [CommitmentResponse.model_validate(item) for item in commitments]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CommitmentResponse)
def create_commitment(
    student_id: int, body: CommitmentInput, user: CurrentUser, db: DbSession
) -> CommitmentResponse:
    commitment = CommitmentService(db).create(user, student_id, body)
    return CommitmentResponse.model_validate(commitment)


@router.patch("/{commitment_id}", response_model=CommitmentResponse)
def update_commitment(
    student_id: int,
    commitment_id: int,
    body: CommitmentUpdate,
    user: CurrentUser,
    db: DbSession,
) -> CommitmentResponse:
    commitment = CommitmentService(db).update(user, student_id, commitment_id, body)
    return CommitmentResponse.model_validate(commitment)
