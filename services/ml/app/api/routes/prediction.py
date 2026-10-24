from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.model_store import ModelBundle
from app.schemas.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelInfo,
    Prediction,
    PredictionRequest,
)
from app.services.predictor import predict

router = APIRouter(prefix="/v1", tags=["prediction"])


def get_model(request: Request) -> ModelBundle:
    model: ModelBundle | None = request.app.state.model
    if model is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model not loaded")
    return model


LoadedModel = Annotated[ModelBundle, Depends(get_model)]


@router.get("/model", response_model=ModelInfo)
def model_info(model: LoadedModel) -> ModelInfo:
    return ModelInfo.model_validate(model.metadata)


@router.post("/predict", response_model=Prediction)
def predict_one(body: PredictionRequest, model: LoadedModel) -> Prediction:
    return predict(model, [body])[0]


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(body: BatchPredictionRequest, model: LoadedModel) -> BatchPredictionResponse:
    return BatchPredictionResponse(model_version=model.version, items=predict(model, body.items))
