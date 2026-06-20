from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.events.base import DomainEvent

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class UserRegistered(DomainEvent):
    user_id: UUID
    email: str
