from dataclasses import dataclass
from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.events.base import DomainEvent

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class TaskCreated(DomainEvent):
    task_id: UUID
    owner_id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class TaskCompleted(DomainEvent):
    task_id: UUID
