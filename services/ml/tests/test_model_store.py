from pathlib import Path

from app.model_store import ModelBundle, load_model, save_model


def test_save_and_load_roundtrip(trained_bundle: ModelBundle, tmp_path: Path) -> None:
    save_model(trained_bundle, tmp_path)

    loaded = load_model(tmp_path)

    assert loaded is not None
    assert loaded.version == trained_bundle.version
    assert loaded.features == trained_bundle.features
    assert loaded.baseline == trained_bundle.baseline


def test_load_returns_none_when_files_are_missing(tmp_path: Path) -> None:
    assert load_model(tmp_path) is None
