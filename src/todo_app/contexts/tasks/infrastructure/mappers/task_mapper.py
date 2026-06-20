from __future__ import annotations

from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus
from todo_app.contexts.tasks.infrastructure.db.models.task_model import TaskModel


class TaskMapper:
    @staticmethod
    def to_entity(model: TaskModel) -> Task:
        return Task(
            id=TaskId(model.id),
            tenant_id=TenantId(model.tenant_id),
            owner_id=OwnerId(model.owner_id),
            title=model.title,
            description=model.description,
            status=TaskStatus.parse(model.status),
            due_date=model.due_date,
        )

    @staticmethod
    def to_model(entity: Task) -> TaskModel:
        return TaskModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            owner_id=entity.owner_id.value,
            title=entity.title,
            description=entity.description,
            status=entity.status.value,
            due_date=entity.due_date,
        )

    @staticmethod
    def apply(entity: Task, model: TaskModel) -> None:
        model.title = entity.title
        model.description = entity.description
        model.status = entity.status.value
        model.due_date = entity.due_date
