from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import ImportKind, ImportStatus
from app.domain.types import BigIntPK


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    uploaded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    kind: Mapped[ImportKind] = mapped_column(Enum(ImportKind, name="import_kind"))
    filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus, name="import_status"))
    rows_ok: Mapped[int] = mapped_column(default=0)
    rows_failed: Mapped[int] = mapped_column(default=0)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
