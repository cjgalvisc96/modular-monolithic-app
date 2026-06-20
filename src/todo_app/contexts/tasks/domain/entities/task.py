"""Task aggregate root.

The owner is referenced by a `UserId` value object — **not** a `User` entity —
to preserve bounded-context isolation. The `tasks` context never imports `users`
internals; it only knows an opaque owner identifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.entities.aggregate import AggregateRoot
from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.shared.domain.value_objects.identifier import EntityId
from todo_app.contexts.tasks.domain.events import TaskCompleted, TaskCreated
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus

if TYPE_CHECKING:
    from datetime import date

    from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId


class OwnerId(EntityId):
    """Opaque reference to the owning user (a UserId from the users context)."""


@dataclass(eq=False)
class Task(AggregateRoot):
    id: TaskId
    tenant_id: TenantId
    owner_id: OwnerId
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    due_date: date | None = None

    def __post_init__(self) -> None:
        super().__init__()
        if not self.title.strip():
            raise DomainValidationError("Task title must not be empty")
        self.title = self.title.strip()

    @classmethod
    def create(
        cls,
        *,
        tenant_id: TenantId,
        owner_id: OwnerId,
        title: str,
        description: str = "",
        due_date: date | None = None,
        task_id: TaskId | None = None,
    ) -> Task:
        task = cls(
            id=task_id or TaskId.generate(),
            tenant_id=tenant_id,
            owner_id=owner_id,
            title=title,
            description=description,
            due_date=due_date,
        )
        task.record_event(
            TaskCreated(
                tenant_id=tenant_id.value,
                task_id=task.id.value,
                owner_id=owner_id.value,
                title=task.title,
            )
        )
        return task

    def complete(self) -> None:
        if self.status is TaskStatus.COMPLETED:
            return
        self.status = TaskStatus.COMPLETED
        self.record_event(TaskCompleted(tenant_id=self.tenant_id.value, task_id=self.id.value))

    def start(self) -> None:
        if self.status is TaskStatus.COMPLETED:
            raise DomainValidationError("Cannot start a completed task")
        self.status = TaskStatus.IN_PROGRESS

    def update_details(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        due_date: date | None = None,
    ) -> None:
        if title is not None:
            if not title.strip():
                raise DomainValidationError("Task title must not be empty")
            self.title = title.strip()
        if description is not None:
            self.description = description
        if due_date is not None:
            self.due_date = due_date
