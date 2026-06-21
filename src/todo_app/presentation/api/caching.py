from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from todo_app.contexts.shared.infrastructure.cache.redis_cache import RedisCache


async def cached[M: BaseModel](
    cache: RedisCache,
    namespace: str,
    key: str,
    model: type[M],
    produce: Callable[[], Awaitable[M]],
    *,
    ttl: int = 300,
) -> M:
    hit = await cache.get(namespace, key)
    if hit is not None:
        return model.model_validate_json(hit)
    value = await produce()
    await cache.set(namespace, key, value.model_dump_json(), ttl=ttl)
    return value
