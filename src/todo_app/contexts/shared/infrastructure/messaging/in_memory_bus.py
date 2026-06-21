"""In-memory event publisher implementing the EventPublisher port (local default)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from todo_app.contexts.shared.domain.events.base import DomainEvent

logger = logging.getLogger("todo_app.events")

Handler = Callable[[DomainEvent], Awaitable[None]]


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        logger.info("domain_event", extra={"event": event.name, "id": str(event.event_id)})
        for handler in self._handlers.get(event.name, ()):
            await handler(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
