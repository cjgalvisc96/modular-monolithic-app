from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.exceptions import EntityNotFoundError
from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.shared.domain.events.publisher import EventPublisher
    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository


class CompleteTaskCommand:
    def __init__(self, repository: TaskRepository, publisher: EventPublisher) -> None:
        self._repository = repository
        self._publisher = publisher

    async def execute(self, task_id: UUID) -> TaskOutput:
        task = await self._repository.get(TaskId(task_id))
        if task is None:
            raise EntityNotFoundError("Task", task_id)
        task.complete()
        await self._repository.update(task)
        await self._publisher.publish_all(task.pull_events())
        return TaskOutput.from_entity(task)
