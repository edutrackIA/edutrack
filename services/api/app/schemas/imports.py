from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain import ImportKind, ImportStatus


class ImportErrorItem(BaseModel):
    row: int | None
    column: str | None
    message: str


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: ImportKind
    filename: str
    status: ImportStatus
    rows_ok: int
    rows_failed: int
    errors: list[ImportErrorItem]
    created_at: datetime
