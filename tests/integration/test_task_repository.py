from __future__ import annotations

import pytest

from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId

pytestmark = pytest.mark.asyncio


async def _add_task(container, tenant_id, title="T"):
    repo = container.tasks.task_repository()
    uow = container.shared.unit_of_work()
    task = Task.create(tenant_id=TenantId(tenant_id), owner_id=OwnerId.generate(), title=title)
    async with uow.begin(tenant_id):
        await repo.add(task)
    return task


async def test_add_complete_and_soft_delete(container, tenant_id):
    repo = container.tasks.task_repository()
    uow = container.shared.unit_of_work()
    task = await _add_task(container, tenant_id, "Do it")

    async with uow.begin(tenant_id):
        loaded = await repo.get(task.id)
        loaded.complete()
        await repo.update(loaded)

    async with uow.begin(tenant_id):
        assert (await repo.get(task.id)).status.value == "completed"

    async with uow.begin(tenant_id):
        await repo.delete(task.id)

    async with uow.begin(tenant_id):
        # soft-deleted rows are invisible to the repository
        assert await repo.get(task.id) is None


async def test_list_filtering(container, tenant_id):
    repo = container.tasks.task_repository()
    uow = container.shared.unit_of_work()
    await _add_task(container, tenant_id, "A")
    await _add_task(container, tenant_id, "B")
    async with uow.begin(tenant_id):
        assert len(await repo.list()) == 2
        assert await repo.get(TaskId.generate()) is None
