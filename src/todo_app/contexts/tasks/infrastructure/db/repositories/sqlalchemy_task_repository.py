from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from todo_app.contexts.shared.infrastructure.db.scoped_session import current_session
from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository
from todo_app.contexts.tasks.infrastructure.db.models.task_model import TaskModel
from todo_app.contexts.tasks.infrastructure.mappers.task_mapper import TaskMapper

if TYPE_CHECKING:
    from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
    from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
    from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus


class SqlAlchemyTaskRepository(TaskRepository):
    async def add(self, task: Task) -> None:
        session = current_session()
        session.add(TaskMapper.to_model(task))
        await session.flush()

    async def get(self, task_id: TaskId) -> Task | None:
        session = current_session()
        model = await session.get(TaskModel, task_id.value)
        if model is None or model.is_deleted:
            return None
        return TaskMapper.to_entity(model)

    async def list(
        self,
        *,
        owner_id: OwnerId | None = None,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        session = current_session()
        stmt = select(TaskModel).where(TaskModel.deleted_at.is_(None))
        if owner_id is not None:
            stmt = stmt.where(TaskModel.owner_id == owner_id.value)
        if status is not None:
            stmt = stmt.where(TaskModel.status == status.value)
        stmt = stmt.order_by(TaskModel.created_at).limit(limit).offset(offset)
        models = (await session.execute(stmt)).scalars().all()
        return [TaskMapper.to_entity(m) for m in models]

    async def count(
        self, *, owner_id: OwnerId | None = None, status: TaskStatus | None = None
    ) -> int:
        session = current_session()
        stmt = select(func.count()).select_from(TaskModel).where(TaskModel.deleted_at.is_(None))
        if owner_id is not None:
            stmt = stmt.where(TaskModel.owner_id == owner_id.value)
        if status is not None:
            stmt = stmt.where(TaskModel.status == status.value)
        return int((await session.execute(stmt)).scalar_one())

    async def update(self, task: Task) -> None:
        session = current_session()
        model = await session.get(TaskModel, task.id.value)
        if model is None:
            raise ValueError(f"Task not found for update: {task.id}")
        TaskMapper.apply(task, model)
        await session.flush()

    async def delete(self, task_id: TaskId) -> None:
        session = current_session()
        model = await session.get(TaskModel, task_id.value)
        if model is None or model.is_deleted:
            return
        model.deleted_at = datetime.now(UTC)
        await session.flush()
