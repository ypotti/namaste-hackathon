"""Safe, consistent public API error responses."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("math_puzzle_agent.api")


def error_response(request: Request, status_code: int, code: str, message: str, *, headers=None):
    request_id = getattr(request.state, "request_id", None)
    content: dict[str, Any] = {"error": {"code": code, "message": message}}
    if request_id:
        content["error"]["request_id"] = request_id
    return JSONResponse(status_code=status_code, content=content, headers=headers)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return error_response(request, exc.status_code, "http_error", message, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return error_response(request, 422, "validation_error", "Request validation failed")

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception):
        logger.exception(
            "Unhandled API error request_id=%s path=%s",
            getattr(request.state, "request_id", "unknown"),
            request.url.path,
        )
        return error_response(request, 500, "internal_error", "An unexpected error occurred")
