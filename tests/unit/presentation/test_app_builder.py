"""ApiBuilder behaviour: health checks, app assembly, and lifespan — no client/DB."""

from types import SimpleNamespace

from todo_app.presentation.api.app import ApiBuilder, create_app


class _DB:
    def __init__(self, ping_error: Exception | None = None) -> None:
        self._ping_error = ping_error
        self.disposed = False

    async def ping(self) -> None:
        if self._ping_error is not None:
            raise self._ping_error

    async def dispose(self) -> None:
        self.disposed = True


class _Cache:
    def __init__(self, ping_error: Exception | None = None) -> None:
        self._ping_error = ping_error
        self.closed = False

    async def ping(self) -> None:
        if self._ping_error is not None:
            raise self._ping_error

    async def close(self) -> None:
        self.closed = True


def _container(db: _DB, cache: _Cache) -> SimpleNamespace:
    return SimpleNamespace(shared=SimpleNamespace(database=lambda: db, cache=lambda: cache))


async def test_check_dependencies_all_ok():
    builder = ApiBuilder(container=_container(_DB(), _Cache()))
    statuses = await builder.check_dependencies()
    assert statuses == {"database": "ok", "redis": "ok"}


async def test_check_dependencies_reports_errors():
    builder = ApiBuilder(
        container=_container(_DB(RuntimeError("db down")), _Cache(RuntimeError("redis down")))
    )
    statuses = await builder.check_dependencies()
    assert statuses["database"].startswith("error")
    assert statuses["redis"].startswith("error")


def test_create_app_assembles_routes_and_metadata():
    app = create_app(container=_container(_DB(), _Cache()))
    assert app.title == "TODO App"
    paths = {getattr(route, "path", "") for route in app.routes}
    assert "/health" in paths
    assert "/metrics" in paths
    # the three v1 routers were mounted under /api/v1
    assert any("/api/v1/tasks" in p for p in app.openapi()["paths"])


async def test_lifespan_pings_on_enter_and_disposes_on_exit():
    db, cache = _DB(), _Cache()
    builder = ApiBuilder(container=_container(db, cache))
    lifespan = builder._create_lifespan()
    app = SimpleNamespace(state=SimpleNamespace())
    async with lifespan(app):
        assert app.state.container is not None
    assert db.disposed is True
    assert cache.closed is True
