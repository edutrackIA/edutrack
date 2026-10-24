import numpy as np

from app.features import encode
from app.model_store import ModelBundle
from app.schemas.prediction import Factor, Prediction, PredictionRequest

MAX_FACTORS = 5


def predict(bundle: ModelBundle, requests: list[PredictionRequest]) -> list[Prediction]:
    """Predict risk and explain each prediction by occlusion.

    A feature's contribution is how much the probability drops when that single
    feature is replaced by the typical (median) student value.
    """
    names = bundle.features
    raw = [request.features.model_dump(mode="json") for request in requests]
    encoded = [encode(row) for row in raw]
    matrix = np.array([[values[name] for name in names] for values in encoded])
    probabilities = bundle.estimator.predict_proba(matrix)[:, 1]

    samples, width = matrix.shape
    baseline = np.array([bundle.baseline[name] for name in names])
    occluded = np.repeat(matrix, width, axis=0)
    occluded[np.arange(samples * width), np.tile(np.arange(width), samples)] = np.tile(
        baseline, samples
    )
    occluded_probabilities = bundle.estimator.predict_proba(occluded)[:, 1].reshape(samples, width)
    contributions = probabilities[:, None] - occluded_probabilities

    predictions: list[Prediction] = []
    for index, request in enumerate(requests):
        order = np.argsort(-contributions[index])
        factors = [
            Factor(
                feature=names[k],
                value=raw[index][names[k]],
                contribution=round(float(contributions[index, k]), 4),
            )
            for k in order
            if contributions[index, k] > 0
        ][:MAX_FACTORS]
        predictions.append(
            Prediction(
                student_id=request.student_id,
                probability=round(float(probabilities[index]), 4),
                model_version=bundle.version,
                top_factors=factors,
            )
        )
    return predictions
