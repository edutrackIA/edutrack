"""Variance Inflation Factor to detect multicollinearity between predictors."""

import numpy as np
import pandas as pd

VIF_THRESHOLD = 10.0


def compute_vif(frame: pd.DataFrame) -> dict[str, float]:
    values = frame.to_numpy(dtype=float)
    result: dict[str, float] = {}
    for index, column in enumerate(frame.columns):
        target = values[:, index]
        others = np.delete(values, index, axis=1)
        design = np.column_stack([np.ones(len(values)), others])
        coefficients, *_ = np.linalg.lstsq(design, target, rcond=None)
        residuals = target - design @ coefficients
        total = float(((target - target.mean()) ** 2).sum())
        r_squared = 1 - float((residuals**2).sum()) / total if total else 1.0
        result[column] = float("inf") if r_squared >= 1 else 1 / (1 - r_squared)
    return result


def select_features(
    frame: pd.DataFrame, threshold: float = VIF_THRESHOLD
) -> tuple[list[str], dict[str, float]]:
    """Drop the feature with the highest VIF until all are below the threshold."""
    columns = list(frame.columns)
    while len(columns) > 1:
        vif = compute_vif(frame[columns])
        worst = max(vif, key=lambda name: vif[name])
        if vif[worst] <= threshold:
            return columns, vif
        columns.remove(worst)
    return columns, compute_vif(frame[columns])
