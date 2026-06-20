from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput
from todo_app.contexts.tasks.domain.entities.task import OwnerId
from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository


class ListTasksQuery:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        owner_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TaskOutput]:
        tasks = await self._repository.list(
            owner_id=OwnerId(owner_id) if owner_id else None,
            status=TaskStatus.parse(status) if status else None,
            limit=limit,
            offset=offset,
        )
        return [TaskOutput.from_entity(t) for t in tasks]
