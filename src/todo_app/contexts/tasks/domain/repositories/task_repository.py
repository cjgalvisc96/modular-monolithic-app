from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
    from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
    from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus


class TaskRepository(ABC):
    @abstractmethod
    async def add(self, task: Task) -> None: ...

    @abstractmethod
    async def get(self, task_id: TaskId) -> Task | None: ...

    @abstractmethod
    async def list(
        self,
        *,
        owner_id: OwnerId | None = None,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]: ...

    @abstractmethod
    async def count(
        self, *, owner_id: OwnerId | None = None, status: TaskStatus | None = None
    ) -> int: ...

    @abstractmethod
    async def update(self, task: Task) -> None: ...

    @abstractmethod
    async def delete(self, task_id: TaskId) -> None:
        """Soft-delete the task (sets deleted_at)."""
