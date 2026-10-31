"""Client for the ML service's model registry (list, train, activate)."""

from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.core.errors import BadGatewayError, NotFoundError, UnprocessableError

# Training a forest with cross-validation takes a while on a small server.
TRAINING_TIMEOUT = 600.0


class ModelRegistry(Protocol):
    def versions(self) -> list[dict[str, Any]]: ...

    def train(self, rows: list[dict[str, Any]]) -> dict[str, Any]: ...

    def activate(self, version: str) -> dict[str, Any]: ...


class HttpModelRegistry:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.transport = transport

    def versions(self) -> list[dict[str, Any]]:
        return self._call("GET", "/v1/models")

    def train(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return self._call("POST", "/v1/models/train", json={"rows": rows}, timeout=TRAINING_TIMEOUT)

    def activate(self, version: str) -> dict[str, Any]:
        return self._call("POST", f"/v1/models/{version}/activate")

    def _call(self, method: str, path: str, *, timeout: float | None = None, **kwargs: Any) -> Any:
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=timeout or self.timeout,
                transport=self.transport,
                headers={"X-Admin-Token": self.token},
            ) as client:
                response = client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise BadGatewayError("The ML service is not available") from exc
        if response.status_code == 404:
            raise NotFoundError("Unknown model version")
        if response.status_code == 422:
            raise UnprocessableError(str(response.json().get("detail", "Invalid training data")))
        if response.status_code == 403:
            raise BadGatewayError("The ML service rejected the admin token")
        if response.is_error:
            raise BadGatewayError("The ML service failed")
        return response.json()


def get_model_registry() -> ModelRegistry:
    settings = get_settings()
    return HttpModelRegistry(settings.ml_service_url, settings.ml_admin_token)
