from pydantic import BaseModel

from todo_app.presentation.api.caching import cached


class Thing(BaseModel):
    id: int
    name: str


class FakeCache:
    def __init__(self, initial: dict[tuple[str, str], str] | None = None) -> None:
        self.store = dict(initial or {})

    async def get(self, namespace: str, key: str) -> str | None:
        return self.store.get((namespace, key))

    async def set(self, namespace: str, key: str, value: str, *, ttl: int = 300) -> None:
        self.store[(namespace, key)] = value


async def test_cache_miss_produces_and_stores():
    cache = FakeCache()
    calls: list[int] = []

    async def produce() -> Thing:
        calls.append(1)
        return Thing(id=1, name="a")

    result = await cached(cache, "tasks", "k", Thing, produce)  # type: ignore[arg-type]
    assert result.id == 1
    assert len(calls) == 1
    assert cache.store[("tasks", "k")]


async def test_cache_hit_skips_produce():
    cache = FakeCache({("tasks", "k"): Thing(id=2, name="b").model_dump_json()})

    async def produce() -> Thing:
        raise AssertionError("produce must not run on a cache hit")

    result = await cached(cache, "tasks", "k", Thing, produce)  # type: ignore[arg-type]
    assert result.id == 2
    assert result.name == "b"
