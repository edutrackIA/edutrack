from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain import ImportKind, ImportStatus


class ImportErrorItem(BaseModel):
    row: int | None
    column: str | None
    message: str


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # A preview (dry run) is not stored, so it has no id or date.
    id: int | None
    kind: ImportKind
    filename: str
    status: ImportStatus
    rows_ok: int
    rows_failed: int
    errors: list[ImportErrorItem]
    created_at: datetime | None
    preview: bool = False
