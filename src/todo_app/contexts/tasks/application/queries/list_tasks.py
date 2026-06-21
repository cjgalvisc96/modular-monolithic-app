from typing import TYPE_CHECKING

from todo_app.contexts.shared.application.page import Page
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
    ) -> Page[TaskOutput]:
        owner = OwnerId(owner_id) if owner_id else None
        task_status = TaskStatus.parse(status) if status else None
        tasks = await self._repository.list(
            owner_id=owner, status=task_status, limit=limit, offset=offset
        )
        total = await self._repository.count(owner_id=owner, status=task_status)
        items = [TaskOutput.from_entity(t) for t in tasks]
        return Page(items=items, total=total, limit=limit, offset=offset)
