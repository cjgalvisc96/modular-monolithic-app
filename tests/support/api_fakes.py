"""Lightweight fakes for unit-testing the FastAPI presentation layer.

Handlers are invoked **directly** (not through an HTTP client or a database), so
these stand in for the DI container, Unit of Work, use cases, and cache. Keeps
the presentation tests in the unit tier: no FastAPI app, no DB, no network.
"""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any


class FakeUow:
    """Stands in for the Unit of Work; ``begin()`` is a no-op async context manager."""

    def __init__(self) -> None:
        self.begin_calls: list[tuple[Any, ...]] = []

    def begin(self, *args: Any):
        self.begin_calls.append(args)

        @asynccontextmanager
        async def _cm():
            yield

        return _cm()


class FakeCommand:
    """Stands in for a command/query use case: records calls, returns a canned result."""

    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((args, kwargs))
        if self._error is not None:
            raise self._error
        return self._result


class FakeCache:
    """In-memory cache port: get/set plus invalidation and health hooks."""

    def __init__(self, initial: dict[tuple[str, str], str] | None = None) -> None:
        self.store = dict(initial or {})
        self.invalidated: list[tuple[str, str]] = []
        self.closed = False

    async def get(self, namespace: str, key: str) -> str | None:
        return self.store.get((namespace, key))

    async def set(self, namespace: str, key: str, value: str, *, ttl: int = 300) -> None:
        self.store[(namespace, key)] = value

    async def invalidate(self, namespace: str, key: str) -> None:
        self.invalidated.append((namespace, key))

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        self.closed = True


def _const(obj: Any):
    return lambda: obj


def make_container(
    *,
    tasks: dict[str, Any] | None = None,
    users: dict[str, Any] | None = None,
    ai: dict[str, Any] | None = None,
    cache: FakeCache | None = None,
    uow: FakeUow | None = None,
) -> SimpleNamespace:
    """Assemble a fake ApplicationContainer exposing only what handlers reach for.

    Each entry in ``tasks``/``users``/``ai`` maps a factory name (e.g.
    ``create_task_command``) to the object its ``()`` call should return.
    """
    cache = cache if cache is not None else FakeCache()
    shared = SimpleNamespace(cache=_const(cache))
    if uow is not None:
        shared.unit_of_work = _const(uow)
    return SimpleNamespace(
        tasks=SimpleNamespace(**{name: _const(obj) for name, obj in (tasks or {}).items()}),
        users=SimpleNamespace(**{name: _const(obj) for name, obj in (users or {}).items()}),
        ai=SimpleNamespace(**{name: _const(obj) for name, obj in (ai or {}).items()}),
        shared=shared,
    )
