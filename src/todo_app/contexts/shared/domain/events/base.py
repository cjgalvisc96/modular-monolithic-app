"""Base class for cross-context domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """A fact that happened in the domain.

    Events are the sanctioned way for one bounded context to react to another
    without importing its internals. Subclasses add their own payload fields.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tenant_id: UUID | None = None

    @property
    def name(self) -> str:
        return type(self).__name__
