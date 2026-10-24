"""Synthetic student dataset (see ADR-0005). No real student data is used."""

import numpy as np
import pandas as pd

from app.features import FEATURE_NAMES

TARGET = "at_risk"
POSITIVE_RATE = 0.18


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))


def generate_dataset(n_samples: int = 4000, seed: int = 42) -> pd.DataFrame:
    """Generate students whose features share latent drivers, as in a real school.

    `engagement` drives academic behaviour and `support` drives the family context.
    The label comes from a known risk function plus noise, so the model can be
    evaluated against a realistic but controlled ground truth.
    """
    rng = np.random.default_rng(seed)
    n = n_samples

    engagement = rng.normal(0, 1, n)
    support = rng.normal(0, 1, n)

    parent_education = rng.choice(5, n, p=[0.05, 0.2, 0.4, 0.2, 0.15])
    home_internet = rng.random(n) < _sigmoid(1.0 + 0.6 * (parent_education - 2) + 0.4 * support)
    has_study_device = rng.random(n) < _sigmoid(0.8 + 0.5 * (parent_education - 2) + 0.3 * support)
    student_works = rng.random(n) < _sigmoid(-2.6 - 0.7 * support)
    household_size = np.clip(np.round(rng.normal(4.5 + 0.3 * (2 - parent_education), 1.4)), 1, 12)
    family_communication = np.clip(np.round(3 + 0.8 * support + rng.normal(0, 0.8, n)), 1, 5)
    study_hours_week = np.clip(
        np.round(8 + 3 * engagement + 1.5 * support + rng.normal(0, 3, n)), 0, 40
    )

    attendance_rate = np.clip(
        0.92 + 0.03 * engagement + 0.015 * support - 0.05 * student_works + rng.normal(0, 0.03, n),
        0.5,
        1.0,
    )
    late_count = rng.poisson(np.clip(3 - 1.2 * engagement, 0.2, None))
    behavior_rating = np.clip(np.round(3.5 + 0.7 * engagement + rng.normal(0, 0.7, n)), 1, 5)
    avg_score = np.clip(
        13
        + 1.8 * engagement
        + 0.8 * support
        + 0.25 * (parent_education - 2)
        + 0.4 * has_study_device
        + 0.3 * home_internet
        + rng.normal(0, 1.3, n),
        0,
        20,
    )
    failed_subjects = rng.binomial(8, _sigmoid(-(avg_score - 11.0) / 1.2))
    score_trend = rng.normal(0.4 * engagement, 1.0)

    risk = (
        -0.9 * (avg_score - 12.5)
        + 0.5 * failed_subjects
        - 25 * (attendance_rate - 0.9)
        + 0.12 * late_count
        - 0.5 * (behavior_rating - 3)
        - 0.6 * score_trend
        - 0.08 * (study_hours_week - 8)
        - 0.3 * (family_communication - 3)
        + 0.8 * student_works
        - 0.3 * home_internet
        - 0.2 * has_study_device
        + rng.normal(0, 0.8, n)
    )
    at_risk = risk > np.quantile(risk, 1 - POSITIVE_RATE)

    frame = pd.DataFrame(
        {
            "avg_score": np.round(avg_score, 2),
            "failed_subjects": failed_subjects,
            "score_trend": np.round(score_trend, 2),
            "attendance_rate": np.round(attendance_rate, 4),
            "late_count": late_count,
            "behavior_rating": behavior_rating.astype(int),
            "study_hours_week": study_hours_week.astype(int),
            "parent_education": parent_education,
            "home_internet": home_internet.astype(int),
            "has_study_device": has_study_device.astype(int),
            "family_communication": family_communication.astype(int),
            "student_works": student_works.astype(int),
            "household_size": household_size.astype(int),
        }
    )
    frame[TARGET] = at_risk.astype(int)
    return frame[[*FEATURE_NAMES, TARGET]]
