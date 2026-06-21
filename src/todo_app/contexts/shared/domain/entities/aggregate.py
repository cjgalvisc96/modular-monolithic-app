"""Aggregate root base — pure Python, no ORM, no framework."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.events.base import DomainEvent


class AggregateRoot:
    """Base for aggregate roots; records domain events for later publication."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events
