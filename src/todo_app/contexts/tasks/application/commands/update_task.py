from typing import TYPE_CHECKING

from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput, UpdateTaskInput
from todo_app.contexts.tasks.domain.exceptions import TaskNotFoundError
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
from todo_app.core.logging import get_logger

if TYPE_CHECKING:
    from logging import Logger
    from uuid import UUID

    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository


class UpdateTaskCommand:
    def __init__(self, repository: TaskRepository, logger: Logger | None = None) -> None:
        self._repository = repository
        self._logger = logger or get_logger(__name__)

    async def execute(self, task_id: UUID, data: UpdateTaskInput) -> TaskOutput:
        task = await self._repository.get(TaskId(task_id))
        if task is None:
            raise TaskNotFoundError(task_id)
        task.update_details(title=data.title, description=data.description, due_date=data.due_date)
        await self._repository.update(task)
        self._logger.info("task.updated", extra={"task_id": str(task_id)})
        return TaskOutput.from_entity(task)
