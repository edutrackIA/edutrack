import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

MODEL_FILE = "model.joblib"
METADATA_FILE = "model.json"


@dataclass(frozen=True)
class ModelBundle:
    estimator: Any
    metadata: dict[str, Any]

    @property
    def version(self) -> str:
        return str(self.metadata["version"])

    @property
    def features(self) -> list[str]:
        return list(self.metadata["features"])

    @property
    def baseline(self) -> dict[str, float]:
        return dict(self.metadata["baseline"])


def save_model(bundle: ModelBundle, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle.estimator, model_dir / MODEL_FILE)
    (model_dir / METADATA_FILE).write_text(
        json.dumps(bundle.metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_model(model_dir: Path) -> ModelBundle | None:
    model_path, metadata_path = model_dir / MODEL_FILE, model_dir / METADATA_FILE
    if not model_path.exists() or not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return ModelBundle(estimator=joblib.load(model_path), metadata=metadata)
