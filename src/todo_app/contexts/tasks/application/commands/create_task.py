from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.tasks.application.dto.task_dto import CreateTaskInput, TaskOutput
from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.shared.domain.events.publisher import EventPublisher
    from todo_app.contexts.tasks.application.ports.user_lookup import UserLookupPort
    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository


class CreateTaskCommand:
    """Create a task, validating the owner exists via the cross-context port."""

    def __init__(
        self,
        repository: TaskRepository,
        user_lookup: UserLookupPort,
        publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._user_lookup = user_lookup
        self._publisher = publisher

    async def execute(self, tenant_id: UUID, data: CreateTaskInput) -> TaskOutput:
        owner = await self._user_lookup.find(data.owner_id)
        if owner is None or not owner.is_active:
            raise DomainValidationError(f"Owner is not a valid active user: {data.owner_id}")
        task = Task.create(
            tenant_id=TenantId(tenant_id),
            owner_id=OwnerId(data.owner_id),
            title=data.title,
            description=data.description,
            due_date=data.due_date,
        )
        await self._repository.add(task)
        await self._publisher.publish_all(task.pull_events())
        return TaskOutput.from_entity(task)
