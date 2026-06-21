"""Exercises the real cross-context adapters against the DB-backed repositories."""

from uuid import uuid4

import pytest

from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
from todo_app.contexts.users.domain.entities.user import User

pytestmark = pytest.mark.asyncio


async def test_user_lookup_adapter_finds_and_misses(container, tenant_id):
    adapter = container.user_lookup()
    uow = container.shared.unit_of_work()
    user = User.register(tenant_id=TenantId(tenant_id), email=Email("a@b.com"), full_name="Ann")
    async with uow.begin(tenant_id):
        await container.users.user_repository().add(user)

    async with uow.begin(tenant_id):
        summary = await adapter.find(user.id.value)
        assert summary is not None and summary.full_name == "Ann" and summary.is_active
        assert await adapter.find(uuid4()) is None


async def test_task_read_adapter_lists_for_owner(container, tenant_id):
    adapter = container.task_read_port()
    uow = container.shared.unit_of_work()
    owner = OwnerId.generate()
    async with uow.begin(tenant_id):
        repo = container.tasks.task_repository()
        await repo.add(Task.create(tenant_id=TenantId(tenant_id), owner_id=owner, title="A"))
        await repo.add(Task.create(tenant_id=TenantId(tenant_id), owner_id=owner, title="B"))

    async with uow.begin(tenant_id):
        briefs = await adapter.list_for_owner(owner.value)
        assert {b.title for b in briefs} == {"A", "B"}
