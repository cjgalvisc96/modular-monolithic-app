"""Event publisher port — the domain depends on this interface, not an impl."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.events.base import DomainEvent


@runtime_checkable
class EventPublisher(Protocol):
    """Publishes domain events to interested subscribers.

    Implemented by the infrastructure messaging layer (in-memory bus locally,
    EventBridge/SQS in the cloud). The domain only sees this port.
    """

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_all(self, events: list[DomainEvent]) -> None: ...
