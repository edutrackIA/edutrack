"""Feature contract shared by training and inference."""

from collections.abc import Mapping

FEATURE_NAMES: tuple[str, ...] = (
    "avg_score",
    "failed_subjects",
    "score_trend",
    "attendance_rate",
    "late_count",
    "behavior_rating",
    "study_hours_week",
    "parent_education",
    "home_internet",
    "has_study_device",
    "family_communication",
    "student_works",
    "household_size",
)

PARENT_EDUCATION_LEVELS = {
    "NONE": 0,
    "PRIMARY": 1,
    "SECONDARY": 2,
    "TECHNICAL": 3,
    "UNIVERSITY": 4,
}


def encode(features: Mapping[str, object]) -> dict[str, float]:
    """Turn API features into the numeric values the model was trained on."""
    encoded: dict[str, float] = {}
    for name in FEATURE_NAMES:
        value = features[name]
        if name == "parent_education":
            value = PARENT_EDUCATION_LEVELS[str(value)]
        encoded[name] = float(value)  # type: ignore[arg-type]
    return encoded
