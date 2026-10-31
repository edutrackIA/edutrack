from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.domain.enums import ModelAction
from app.domain.types import BigIntPK
from app.domain.user import User


class ModelEvent(Base):
    """Who trained or activated each model version, and when (governance trail)."""

    __tablename__ = "model_events"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    institution_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("institutions.id"))
    version: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[ModelAction] = mapped_column(Enum(ModelAction, name="model_action"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    user: Mapped[User] = relationship()
