"""HTTP boundary middleware for request tracing and basic abuse protection."""

from __future__ import annotations

import logging
import re
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from math_puzzle_agent.api.errors import error_response

logger = logging.getLogger("math_puzzle_agent.api")
_GENERATION_PATH = re.compile(r"^/api/v1/conversations/[^/]+/messages$")


class APIBoundaryMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings, rate_limiter) -> None:
        super().__init__(app)
        self.settings = settings
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        supplied_id = request.headers.get("x-request-id", "")
        request_id = supplied_id if 0 < len(supplied_id) <= 128 else str(uuid.uuid4())
        request.state.request_id = request_id

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                too_large = int(content_length) > self.settings.max_request_body_bytes
            except ValueError:
                too_large = True
            if too_large:
                response = error_response(request, 413, "request_too_large", "Request body is too large")
                return self._secure(response, request_id)

        if request.method == "POST" and _GENERATION_PATH.match(request.url.path):
            client = request.client.host if request.client else "unknown"
            allowed, retry_after = self.rate_limiter.check(client)
            if not allowed:
                response = error_response(
                    request,
                    429,
                    "rate_limit_exceeded",
                    "Too many generation requests",
                    headers={"Retry-After": str(retry_after)},
                )
                return self._secure(response, request_id)

        response = await call_next(request)
        logger.info("API request request_id=%s method=%s path=%s status=%s", request_id, request.method, request.url.path, response.status_code)
        return self._secure(response, request_id)

    @staticmethod
    def _secure(response, request_id: str):
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if response.headers.get("content-type", "").startswith("text/html"):
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'unsafe-inline'; "
                "img-src data:; frame-ancestors 'self'"
            )
        else:
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response
