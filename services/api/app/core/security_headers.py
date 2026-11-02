"""HTTP headers that harden every API response."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

BASE_HEADERS = {
    # The browser must not guess content types (e.g. treat a CSV as HTML).
    "X-Content-Type-Options": "nosniff",
    # The API is never meant to be shown inside a frame.
    "X-Frame-Options": "DENY",
    # Invitation links carry a token in the URL: never leak it to other sites.
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    # Responses contain student data: no shared or browser caches.
    "Cache-Control": "no-store",
}

HSTS = "max-age=31536000; includeSubDomains"


def add_security_headers(app: FastAPI, *, https_only: bool) -> None:
    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for name, value in BASE_HEADERS.items():
            response.headers.setdefault(name, value)
        if https_only:
            response.headers.setdefault("Strict-Transport-Security", HSTS)
        return response
