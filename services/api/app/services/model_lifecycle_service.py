"""Model versions over time: train candidates with school data, activate with approval.

Separation of duties: analysis trains a candidate, direction decides whether it goes live.
Every training and activation is recorded with who did it.
"""

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import UnprocessableError
from app.domain import ModelAction, ModelEvent, User
from app.schemas.model_lifecycle import (
    ModelsOverview,
    ModelVersionView,
    TrainingReadiness,
    TrainingResult,
)
from app.services.model_monitoring_service import ModelMonitoringService
from app.services.risk.model_registry import ModelRegistry

# A forest trained on fewer real cases would mostly learn noise from this school.
MIN_TRAINING_ROWS = 200
MIN_TRAINING_DROPOUTS = 20


class ModelLifecycleService:
    def __init__(self, db: Session, registry: ModelRegistry, today: date) -> None:
        self.db = db
        self.registry = registry
        self.monitoring = ModelMonitoringService(db, today)

    def overview(self, user: User) -> ModelsOverview:
        rows = self.monitoring.training_rows(user)
        dropouts = sum(bool(row["dropout"]) for row in rows)
        events = self._events(user)
        return ModelsOverview(
            versions=[self._view(item, events) for item in self.registry.versions()],
            training=TrainingReadiness(
                labeled=len(rows),
                dropouts=dropouts,
                min_labeled=MIN_TRAINING_ROWS,
                min_dropouts=MIN_TRAINING_DROPOUTS,
                can_train=len(rows) >= MIN_TRAINING_ROWS and dropouts >= MIN_TRAINING_DROPOUTS,
            ),
        )

    def train(self, user: User) -> TrainingResult:
        rows = self.monitoring.training_rows(user)
        dropouts = sum(bool(row["dropout"]) for row in rows)
        if len(rows) < MIN_TRAINING_ROWS or dropouts < MIN_TRAINING_DROPOUTS:
            raise UnprocessableError(
                f"Se necesitan al menos {MIN_TRAINING_ROWS} evaluaciones con resultado conocido "
                f"y {MIN_TRAINING_DROPOUTS} retiros; hay {len(rows)} y {dropouts}.",
                code="NOT_ENOUGH_DATA",
            )
        result = self.registry.train(rows)
        candidate = result["candidate"]
        self._record(user, candidate["version"], ModelAction.TRAINED, {"rows": len(rows)})
        return TrainingResult(
            candidate=self._view(candidate, self._events(user)),
            active_on_holdout=result.get("active_on_holdout"),
        )

    def activate(self, user: User, version: str) -> ModelVersionView:
        activated = self.registry.activate(version)
        self._record(user, version, ModelAction.ACTIVATED, {})
        return self._view(activated, self._events(user))

    # --- Internos ------------------------------------------------------------------------

    def _record(
        self, user: User, version: str, action: ModelAction, details: dict[str, Any]
    ) -> None:
        self.db.add(
            ModelEvent(
                institution_id=user.institution_id,
                version=version,
                action=action,
                user_id=user.id,
                details=details,
            )
        )
        self.db.commit()

    def _events(self, user: User) -> list[ModelEvent]:
        return list(
            self.db.scalars(
                select(ModelEvent)
                .where(ModelEvent.institution_id == user.institution_id)
                .order_by(ModelEvent.created_at, ModelEvent.id)
            )
        )

    @staticmethod
    def _view(item: dict[str, Any], events: list[ModelEvent]) -> ModelVersionView:
        dataset = item.get("dataset") or {}
        trained = [
            e for e in events if e.version == item["version"] and e.action == ModelAction.TRAINED
        ]
        activated = [
            e for e in events if e.version == item["version"] and e.action == ModelAction.ACTIVATED
        ]
        return ModelVersionView(
            version=item["version"],
            trained_at=item.get("trained_at"),
            active=bool(item.get("active")),
            synthetic_samples=dataset.get("synthetic_samples") or dataset.get("n_samples"),
            school_samples=dataset.get("school_samples"),
            school_dropouts=dataset.get("school_dropouts"),
            school_holdout=item.get("school_holdout"),
            trained_by=trained[-1].user.full_name if trained else None,
            activated_by=activated[-1].user.full_name if activated else None,
            activated_at=activated[-1].created_at if activated else None,
        )
