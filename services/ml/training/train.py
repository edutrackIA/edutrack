"""Train the risk model: synthetic data, VIF, SMOTE + Random Forest, evaluation."""

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

from app.features import FEATURE_NAMES
from app.model_store import ModelBundle, save_version, set_active
from training.dataset import TARGET, generate_dataset
from training.vif import select_features

MIN_F1 = 0.75
MIN_ROC_AUC = 0.80

FULL_GRID = {
    "model__n_estimators": [300],
    "model__max_depth": [None, 10],
    "model__min_samples_leaf": [1, 3],
}
QUICK_GRID = {"model__n_estimators": [50], "model__max_depth": [8]}


def fit_search(
    x_train: np.ndarray, y_train: np.ndarray, seed: int, grid: dict[str, Any], folds: int
) -> GridSearchCV:
    """SMOTE + Random Forest tuned by cross-validated F1.

    SMOTE lives inside the pipeline so it only oversamples training folds:
    validation folds and the test set keep the real class balance.
    """
    pipeline = Pipeline(
        [
            ("smote", SMOTE(random_state=seed)),
            ("model", RandomForestClassifier(random_state=seed, n_jobs=-1)),
        ]
    )
    search = GridSearchCV(
        pipeline,
        grid,
        scoring="f1",
        cv=StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed),
    )
    search.fit(x_train, y_train)
    return search


@dataclass
class TrainingResult:
    bundle: ModelBundle


def train(n_samples: int = 4000, seed: int = 42, quick: bool = False) -> TrainingResult:
    data = generate_dataset(n_samples, seed)
    features, vif = select_features(data[list(FEATURE_NAMES)])

    x_train, x_test, y_train, y_test = train_test_split(
        data[features].to_numpy(dtype=float),
        data[TARGET].to_numpy(),
        test_size=0.2,
        stratify=data[TARGET],
        random_state=seed,
    )

    search = fit_search(
        x_train, y_train, seed, QUICK_GRID if quick else FULL_GRID, 3 if quick else 5
    )
    model: RandomForestClassifier = search.best_estimator_.named_steps["model"]

    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "f1": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "precision": round(float(precision_score(y_test, predictions)), 4),
        "recall": round(float(recall_score(y_test, predictions)), 4),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "cv_f1": round(float(search.best_score_), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }

    trained_at = datetime.now(UTC)
    metadata: dict[str, Any] = {
        "version": f"rf-{trained_at:%Y.%m.%d}-{seed}",
        "algorithm": "RandomForestClassifier",
        "trained_at": trained_at.isoformat(),
        "sklearn_version": sklearn.__version__,
        "features": features,
        "baseline": {
            name: float(value)
            for name, value in zip(features, np.median(x_train, axis=0), strict=True)
        },
        "metrics": metrics,
        "vif": {name: round(value, 3) for name, value in vif.items()},
        "feature_importances": {
            name: round(float(value), 4)
            for name, value in zip(features, model.feature_importances_, strict=True)
        },
        "best_params": search.best_params_,
        "dataset": {
            "samples": n_samples,
            "seed": seed,
            "positive_rate": round(float(data[TARGET].mean()), 4),
        },
    }
    return TrainingResult(bundle=ModelBundle(estimator=model, metadata=metadata))


def meets_requirements(metrics: dict[str, Any]) -> bool:
    return metrics["f1"] >= MIN_F1 and metrics["roc_auc"] > MIN_ROC_AUC


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train the EduTrack risk model.")
    parser.add_argument("--samples", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quick", action="store_true", help="small grid for smoke tests")
    parser.add_argument("--output", type=Path, default=Path("models"))
    parser.add_argument("--export-dataset", type=Path, default=None)
    args = parser.parse_args(argv)

    result = train(args.samples, args.seed, args.quick)
    # Registered as a new version and activated, so the service picks it up on restart.
    save_version(result.bundle, args.output)
    set_active(args.output, result.bundle.version)
    if args.export_dataset is not None:
        args.export_dataset.parent.mkdir(parents=True, exist_ok=True)
        generate_dataset(args.samples, args.seed).to_csv(args.export_dataset, index=False)

    metadata = result.bundle.metadata
    metrics = metadata["metrics"]
    print(f"Model {metadata['version']} saved to {args.output}")
    print(f"Features ({len(metadata['features'])}): {', '.join(metadata['features'])}")
    print(f"Max VIF: {max(metadata['vif'].values()):.2f}")
    for name in ("f1", "roc_auc", "precision", "recall", "accuracy", "cv_f1"):
        print(f"  {name:<10} {metrics[name]:.4f}")
    print(f"  confusion  {metrics['confusion_matrix']}")

    if meets_requirements(metrics):
        print(f"RNF-02 met: F1 >= {MIN_F1} and ROC-AUC > {MIN_ROC_AUC}")
        return 0
    print(f"RNF-02 NOT met: F1 >= {MIN_F1} and ROC-AUC > {MIN_ROC_AUC} required")
    return 1


if __name__ == "__main__":
    sys.exit(main())
