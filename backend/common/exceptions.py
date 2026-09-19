"""
Custom exceptions and global error handler.

Raise these in services; the handler converts them to proper HTTP responses.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


# ── Base ─────────────────────────────────────────────────


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ── Domain errors ────────────────────────────────────────


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        msg = f"{resource} not found"
        if resource_id:
            msg = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=msg, status_code=404)


class BadRequestError(AppError):
    """Invalid input / validation error."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message=message, status_code=400)


class ConflictError(AppError):
    """Resource already exists."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class AIServiceError(AppError):
    """AI / LLM service failure."""

    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message=message, status_code=503)


# ── Global handler ───────────────────────────────────────


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )
