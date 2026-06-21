"""Namespace-aware Redis cache wrapper (keys stored as ``<namespace>:<key>``)."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisCache:
    def __init__(
        self, redis: Redis, *, enabled: bool = True, namespaces: tuple[str, ...] = ()
    ) -> None:
        self._redis = redis
        self._enabled = enabled
        self._namespaces = set(namespaces)

    def _key(self, namespace: str, key: str) -> str:
        if self._namespaces and namespace not in self._namespaces:
            raise ValueError(f"Unknown cache namespace: {namespace}")
        return f"{namespace}:{key}"

    async def get(self, namespace: str, key: str) -> str | None:
        if not self._enabled:
            return None
        value = await self._redis.get(self._key(namespace, key))
        return value.decode() if isinstance(value, bytes) else value

    async def set(self, namespace: str, key: str, value: str, *, ttl: int = 300) -> None:
        if not self._enabled:
            return
        await self._redis.set(self._key(namespace, key), value, ex=ttl)

    async def invalidate(self, namespace: str, key: str) -> None:
        if not self._enabled:
            return
        await self._redis.delete(self._key(namespace, key))

    async def ping(self) -> bool:
        if not self._enabled:
            return True
        return bool(await self._redis.ping())

    async def close(self) -> None:
        await self._redis.aclose()
