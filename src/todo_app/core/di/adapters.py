"""Cross-context adapters wired at the composition root, keeping contexts isolated."""

from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.ai.application.ports.task_read_port import TaskBrief, TaskReadPort
from todo_app.contexts.tasks.application.ports.user_lookup import (
    UserLookupPort,
    UserSummary,
)
from todo_app.contexts.tasks.domain.entities.task import OwnerId
from todo_app.contexts.users.domain.value_objects.user_id import UserId

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository
    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository


class UsersUserLookupAdapter(UserLookupPort):
    """Satisfies tasks' UserLookupPort from the users repository."""

    def __init__(self, user_repository_factory: Callable[[], UserRepository]) -> None:
        self._factory = user_repository_factory

    async def find(self, user_id: UUID) -> UserSummary | None:
        repo = self._factory()
        user = await repo.get(UserId(user_id))
        if user is None:
            return None
        return UserSummary(id=user.id.value, full_name=user.full_name, is_active=user.is_active)


class TasksTaskReadAdapter(TaskReadPort):
    """Satisfies ai's TaskReadPort from the tasks repository."""

    def __init__(self, task_repository_factory: Callable[[], TaskRepository]) -> None:
        self._factory = task_repository_factory

    async def list_for_owner(self, owner_id: UUID, *, limit: int = 20) -> list[TaskBrief]:
        repo = self._factory()
        tasks = await repo.list(owner_id=OwnerId(owner_id), limit=limit)
        return [TaskBrief(title=t.title, status=t.status.value) for t in tasks]
