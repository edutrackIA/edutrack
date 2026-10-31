from pathlib import Path

import numpy as np
import pandas as pd

from app.features import FEATURE_NAMES
from app.model_store import load_active
from training.dataset import TARGET, generate_dataset
from training.train import main, meets_requirements
from training.vif import compute_vif, select_features


def test_dataset_has_expected_shape_and_balance() -> None:
    data = generate_dataset(n_samples=1000, seed=3)

    assert list(data.columns) == [*FEATURE_NAMES, TARGET]
    assert len(data) == 1000
    assert 0.17 <= data[TARGET].mean() <= 0.19
    assert data["avg_score"].between(0, 20).all()
    assert data["attendance_rate"].between(0.5, 1).all()


def test_dataset_is_reproducible() -> None:
    pd.testing.assert_frame_equal(generate_dataset(200, 5), generate_dataset(200, 5))


def test_vif_flags_and_removes_collinear_features() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=500)
    frame = pd.DataFrame(
        {"x": x, "x_copy": 2 * x + rng.normal(0, 0.01, 500), "z": rng.normal(size=500)}
    )

    vif = compute_vif(frame)
    selected, final_vif = select_features(frame)

    assert vif["x"] > 10 and vif["x_copy"] > 10
    assert vif["z"] < 2
    assert len(selected) == 2 and "z" in selected
    assert max(final_vif.values()) < 10


def test_requirement_check() -> None:
    assert meets_requirements({"f1": 0.8, "roc_auc": 0.9})
    assert not meets_requirements({"f1": 0.7, "roc_auc": 0.9})
    assert not meets_requirements({"f1": 0.8, "roc_auc": 0.8})


def test_cli_trains_and_saves_model(tmp_path: Path) -> None:
    dataset = tmp_path / "data.csv"

    exit_code = main(
        [
            "--samples",
            "400",
            "--quick",
            "--output",
            str(tmp_path / "models"),
            "--export-dataset",
            str(dataset),
        ]
    )

    assert exit_code in (0, 1)
    assert load_active(tmp_path / "models") is not None
    assert dataset.exists()
