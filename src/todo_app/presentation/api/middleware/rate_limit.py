from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

_EXEMPT = frozenset({"/health", "/metrics", "/", "/docs", "/redoc", "/openapi.json"})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed fixed-window rate limit keyed by client IP; fails open if Redis is down."""

    def __init__(self, app: object, *, limit: int, window: int, enabled: bool = True) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._limit = limit
        self._window = window
        self._enabled = enabled

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not self._enabled or request.url.path in _EXEMPT:
            return await call_next(request)

        count = await self._hit(request)
        if count is not None and count > self._limit:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "detail": "Too many requests"},
                headers={"Retry-After": str(self._window)},
            )
        return await call_next(request)

    async def _hit(self, request: Request) -> int | None:
        container = getattr(request.app.state, "container", None)
        if container is None:
            return None
        client = request.client.host if request.client else "unknown"
        try:
            redis = container.shared.redis()
            count = await redis.incr(f"ratelimit:{client}")
            if count == 1:
                await redis.expire(f"ratelimit:{client}", self._window)
            return int(count)
        except Exception:
            return None
