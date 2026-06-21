"""Request-context middleware: correlation id + logging (tenant binding is in the dependency)."""

import logging
import time
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from todo_app.contexts.shared.application.request_context import current_context

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger("todo_app.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        ctx = current_context()
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "elapsed_ms": round(elapsed_ms, 2),
                "tenant_id": str(ctx.tenant_id) if ctx else None,
            },
        )
        response.headers["x-request-id"] = request_id
        return response
