from typing import TYPE_CHECKING

from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput
from todo_app.contexts.tasks.domain.exceptions import TaskNotFoundError
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
from todo_app.core.logging import get_logger

if TYPE_CHECKING:
    from logging import Logger
    from uuid import UUID

    from todo_app.contexts.shared.domain.events.publisher import EventPublisher
    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository


class CompleteTaskCommand:
    def __init__(
        self,
        repository: TaskRepository,
        publisher: EventPublisher,
        logger: Logger | None = None,
    ) -> None:
        self._repository = repository
        self._publisher = publisher
        self._logger = logger or get_logger(__name__)

    async def execute(self, task_id: UUID) -> TaskOutput:
        task = await self._repository.get(TaskId(task_id))
        if task is None:
            raise TaskNotFoundError(task_id)
        task.complete()
        await self._repository.update(task)
        await self._publisher.publish_all(task.pull_events())
        self._logger.info("task.completed", extra={"task_id": str(task_id)})
        return TaskOutput.from_entity(task)
