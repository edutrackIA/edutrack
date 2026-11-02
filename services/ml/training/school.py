"""Retrain the model with a school's real outcomes on top of the synthetic dataset.

A part of the school's cases is held out and never used for training: both the active
model and the candidate are scored on exactly those cases, so the comparison reflects
how each one does with this school's real students.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.features import FEATURE_NAMES, encode
from app.model_store import ModelBundle
from training.dataset import TARGET, generate_dataset
from training.train import fit_search
from training.vif import select_features

SCHOOL_GRID = {"model__n_estimators": [200], "model__max_depth": [None, 10]}
HOLDOUT_SHARE = 0.3
# Real cases count more than synthetic ones: they are what the school actually looks like.
SCHOOL_WEIGHT = 5
MIN_ROWS = 20
MIN_PER_CLASS = 5


@dataclass
class SchoolTraining:
    bundle: ModelBundle
    holdout: pd.DataFrame


def school_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Encode the API's feature rows the same way predictions are encoded."""
    frame = pd.DataFrame([encode(row["features"]) for row in rows])
    frame[TARGET] = [int(bool(row["dropout"])) for row in rows]
    return frame


def check_enough(frame: pd.DataFrame) -> None:
    positives = int(frame[TARGET].sum())
    if len(frame) < MIN_ROWS or positives < MIN_PER_CLASS or len(frame) - positives < MIN_PER_CLASS:
        raise ValueError(
            f"Need at least {MIN_ROWS} rows and {MIN_PER_CLASS} of each outcome; "
            f"got {len(frame)} rows and {positives} dropouts"
        )


def score(bundle: ModelBundle, holdout: pd.DataFrame) -> dict[str, float | int | None]:
    """How a model does on the held-out real cases, at the default 0.5 cut."""
    matrix = holdout[bundle.features].to_numpy(dtype=float)
    truth = holdout[TARGET].to_numpy()
    probabilities = bundle.estimator.predict_proba(matrix)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    both_classes = len(set(truth.tolist())) == 2
    return {
        "cases": len(holdout),
        "dropouts": int(truth.sum()),
        "recall": round(float(recall_score(truth, predictions, zero_division=0)), 4),
        "precision": round(float(precision_score(truth, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(truth, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(truth, probabilities)), 4) if both_classes else None,
    }


def train_with_school_data(
    rows: list[dict[str, Any]], seed: int = 42, synthetic_samples: int = 4000
) -> SchoolTraining:
    school = school_frame(rows)
    check_enough(school)
    school_train, holdout = train_test_split(
        school, test_size=HOLDOUT_SHARE, stratify=school[TARGET], random_state=seed
    )

    synthetic = generate_dataset(synthetic_samples, seed)[[*FEATURE_NAMES, TARGET]]
    data = pd.concat([synthetic, *([school_train] * SCHOOL_WEIGHT)], ignore_index=True).astype(
        float
    )
    features, vif = select_features(data[list(FEATURE_NAMES)])
    x_train = data[features].to_numpy(dtype=float)
    y_train = data[TARGET].to_numpy().astype(int)

    search = fit_search(x_train, y_train, seed, SCHOOL_GRID, folds=3)
    model = search.best_estimator_.named_steps["model"]

    trained_at = datetime.now(UTC)
    bundle = ModelBundle(
        estimator=model,
        metadata={
            "version": f"rf-{trained_at:%Y.%m.%d-%H%M%S}-school",
            "algorithm": "RandomForestClassifier",
            "trained_at": trained_at.isoformat(),
            "sklearn_version": sklearn.__version__,
            "features": features,
            "baseline": {
                name: float(value)
                for name, value in zip(features, np.median(x_train, axis=0), strict=True)
            },
            "metrics": {"cv_f1": round(float(search.best_score_), 4)},
            "vif": {name: round(value, 3) for name, value in vif.items()},
            "best_params": search.best_params_,
            "dataset": {
                "synthetic_samples": synthetic_samples,
                "school_samples": len(school_train),
                "school_dropouts": int(school_train[TARGET].sum()),
                "school_weight": SCHOOL_WEIGHT,
                "seed": seed,
            },
        },
    )
    bundle.metadata["school_holdout"] = score(bundle, holdout)
    return SchoolTraining(bundle=bundle, holdout=holdout)
