from __future__ import annotations

from fastapi import FastAPI
from starlette.testclient import TestClient

from todo_app.presentation.api.middleware.rate_limit import RateLimitMiddleware


class FakeRedis:
    def __init__(self, *, broken: bool = False) -> None:
        self._counts: dict[str, int] = {}
        self._broken = broken

    async def incr(self, key: str) -> int:
        if self._broken:
            raise ConnectionError("redis down")
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    async def expire(self, key: str, ttl: int) -> None:
        pass


class FakeContainer:
    def __init__(self, redis: FakeRedis) -> None:
        self.shared = type("S", (), {"redis": lambda _self: redis})()


def _app(redis: FakeRedis | None = None, *, limit: int = 2, enabled: bool = True) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limit=limit, window=60, enabled=enabled)

    @app.get("/x")
    def x() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    if redis is not None:
        app.state.container = FakeContainer(redis)
    return TestClient(app)


def test_allows_under_limit_then_blocks():
    client = _app(FakeRedis(), limit=2)
    assert client.get("/x").status_code == 200
    assert client.get("/x").status_code == 200
    assert client.get("/x").status_code == 429


def test_exempt_paths_never_limited():
    client = _app(FakeRedis(), limit=1)
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200


def test_disabled_passes_through():
    client = _app(FakeRedis(), limit=1, enabled=False)
    assert client.get("/x").status_code == 200
    assert client.get("/x").status_code == 200


def test_fails_open_without_container():
    client = _app(redis=None, limit=1)
    assert client.get("/x").status_code == 200
    assert client.get("/x").status_code == 200


def test_fails_open_when_redis_broken():
    client = _app(FakeRedis(broken=True), limit=1)
    assert client.get("/x").status_code == 200
    assert client.get("/x").status_code == 200
