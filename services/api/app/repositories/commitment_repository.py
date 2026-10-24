from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import Commitment


class CommitmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, commitment_id: int) -> Commitment | None:
        return self.db.get(Commitment, commitment_id)

    def list_for_student(self, student_id: int) -> list[Commitment]:
        query = (
            select(Commitment)
            .where(Commitment.student_id == student_id)
            .order_by(Commitment.meeting_date.desc(), Commitment.id.desc())
        )
        return list(self.db.scalars(query))

    def add(self, commitment: Commitment) -> Commitment:
        self.db.add(commitment)
        self.db.flush()
        return commitment
