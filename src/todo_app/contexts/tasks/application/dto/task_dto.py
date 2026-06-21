from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from todo_app.contexts.tasks.domain.entities.task import Task


@dataclass(frozen=True, slots=True)
class CreateTaskInput:
    owner_id: UUID
    title: str
    description: str = ""
    due_date: date | None = None


@dataclass(frozen=True, slots=True)
class UpdateTaskInput:
    title: str | None = None
    description: str | None = None
    due_date: date | None = None


@dataclass(frozen=True, slots=True)
class TaskOutput:
    id: UUID
    tenant_id: UUID
    owner_id: UUID
    title: str
    description: str
    status: str
    due_date: date | None

    @classmethod
    def from_entity(cls, task: Task) -> TaskOutput:
        return cls(
            id=task.id.value,
            tenant_id=task.tenant_id.value,
            owner_id=task.owner_id.value,
            title=task.title,
            description=task.description,
            status=task.status.value,
            due_date=task.due_date,
        )
