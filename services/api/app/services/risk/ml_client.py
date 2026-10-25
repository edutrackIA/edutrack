from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.core.errors import BadGatewayError

BATCH_SIZE = 500


class MlClient(Protocol):
    def predict_batch(self, items: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]: ...


class HttpMlClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.transport = transport

    def predict_batch(self, items: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        version = ""
        predictions: list[dict[str, Any]] = []
        try:
            with httpx.Client(
                base_url=self.base_url, timeout=self.timeout, transport=self.transport
            ) as client:
                for start in range(0, len(items), BATCH_SIZE):
                    response = client.post(
                        "/v1/predict/batch", json={"items": items[start : start + BATCH_SIZE]}
                    )
                    response.raise_for_status()
                    body = response.json()
                    version = body["model_version"]
                    predictions.extend(body["items"])
        except httpx.HTTPError as exc:
            raise BadGatewayError("The ML service is not available") from exc
        return version, predictions


def get_ml_client() -> MlClient:
    return HttpMlClient(get_settings().ml_service_url)
