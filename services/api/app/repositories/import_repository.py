from sqlalchemy.orm import Session

from app.domain import ImportJob


class ImportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, job_id: int) -> ImportJob | None:
        return self.db.get(ImportJob, job_id)

    def add(self, job: ImportJob) -> ImportJob:
        self.db.add(job)
        self.db.flush()
        return job
