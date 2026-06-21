"""Maps domain exceptions to HTTP responses at the transport boundary.

The domain raises framework-free errors; only here do they become status codes.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from todo_app.contexts.shared.domain.exceptions import (
    ConflictError,
    DomainValidationError,
    EntityNotFoundError,
    PermissionDeniedError,
)

_STATUS_MAP = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DomainValidationError: 422,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
}


def register_exception_handlers(app: FastAPI) -> None:
    async def _handle(request: Request, exc: Exception) -> JSONResponse:
        code = next(
            (c for t, c in _STATUS_MAP.items() if isinstance(exc, t)),
            status.HTTP_400_BAD_REQUEST,
        )
        return JSONResponse(
            status_code=code,
            content={"error": type(exc).__name__, "detail": str(exc)},
        )

    for exc_type in _STATUS_MAP:
        app.add_exception_handler(exc_type, _handle)
