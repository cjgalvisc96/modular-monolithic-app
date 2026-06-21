"""SharedContainer — composition root; the only place allowed to wire all three layers."""

from dependency_injector import containers, providers
from redis.asyncio import Redis

from todo_app.contexts.shared.infrastructure.cache.redis_cache import RedisCache
from todo_app.contexts.shared.infrastructure.db.session import Database
from todo_app.contexts.shared.infrastructure.db.unit_of_work import UnitOfWork
from todo_app.contexts.shared.infrastructure.messaging.in_memory_bus import (
    InMemoryEventPublisher,
)


class SharedContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    database = providers.Singleton(
        Database,
        dsn=config.database_dsn,
        echo=config.db_echo,
        pool_size=config.db_pool_size,
        max_overflow=config.db_pool_max_overflow,
    )

    unit_of_work = providers.Factory(UnitOfWork, database=database)

    redis = providers.Singleton(Redis.from_url, config.redis_dsn)

    cache = providers.Singleton(
        RedisCache,
        redis=redis,
        enabled=config.cache_enable,
        namespaces=config.cache_namespace_tuple,
    )

    event_publisher = providers.Singleton(InMemoryEventPublisher)
