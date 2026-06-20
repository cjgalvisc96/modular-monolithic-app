from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.exceptions import EntityNotFoundError
from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput, UpdateTaskInput
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository


class UpdateTaskCommand:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def execute(self, task_id: UUID, data: UpdateTaskInput) -> TaskOutput:
        task = await self._repository.get(TaskId(task_id))
        if task is None:
            raise EntityNotFoundError("Task", task_id)
        task.update_details(title=data.title, description=data.description, due_date=data.due_date)
        await self._repository.update(task)
        return TaskOutput.from_entity(task)
