"""Model files on disk: a registry of versions and which one is active.

Layout of the model directory:

    versions/<version>/model.joblib
    versions/<version>/model.json
    active.json                      {"version": "<version>"}

Older installs kept a single model in the root of the directory; it is moved into the
registry the first time the service starts.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

MODEL_FILE = "model.joblib"
METADATA_FILE = "model.json"
VERSIONS_DIR = "versions"
ACTIVE_FILE = "active.json"


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


# --- Registro de versiones ---------------------------------------------------------------


def version_dir(root: Path, version: str) -> Path:
    if not version or "/" in version or "\\" in version or version.startswith("."):
        raise ValueError(f"Invalid model version: {version!r}")
    return root / VERSIONS_DIR / version


def save_version(bundle: ModelBundle, root: Path) -> None:
    save_model(bundle, version_dir(root, bundle.version))


def list_versions(root: Path) -> list[dict[str, Any]]:
    """Metadata of every stored version, newest first."""
    folder = root / VERSIONS_DIR
    if not folder.exists():
        return []
    versions = [
        json.loads((path / METADATA_FILE).read_text(encoding="utf-8"))
        for path in folder.iterdir()
        if (path / METADATA_FILE).exists()
    ]
    return sorted(versions, key=lambda item: str(item.get("trained_at", "")), reverse=True)


def active_version(root: Path) -> str | None:
    path = root / ACTIVE_FILE
    if not path.exists():
        return None
    return str(json.loads(path.read_text(encoding="utf-8"))["version"])


def set_active(root: Path, version: str) -> ModelBundle:
    bundle = load_model(version_dir(root, version))
    if bundle is None:
        raise FileNotFoundError(version)
    (root / ACTIVE_FILE).write_text(json.dumps({"version": version}), encoding="utf-8")
    return bundle


def load_active(root: Path) -> ModelBundle | None:
    version = active_version(root)
    if version is not None:
        return load_model(version_dir(root, version))
    legacy = load_model(root)
    if legacy is None:
        return None
    # First start after the upgrade: the single model becomes the first version.
    save_version(legacy, root)
    return set_active(root, legacy.version)
