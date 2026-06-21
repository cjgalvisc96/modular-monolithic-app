"""Repository integration tests against a real (SQLite) database via the UoW."""

import pytest

from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.users.domain.entities.user import User
from todo_app.contexts.users.domain.value_objects.user_id import UserId

pytestmark = pytest.mark.asyncio


async def test_add_get_and_update_user(container, tenant_id):
    repo = container.users.user_repository()
    uow = container.shared.unit_of_work()

    user = User.register(tenant_id=TenantId(tenant_id), email=Email("a@b.com"), full_name="Ann")
    async with uow.begin(tenant_id):
        await repo.add(user)

    async with uow.begin(tenant_id):
        fetched = await repo.get(user.id)
        assert fetched is not None
        assert str(fetched.email) == "a@b.com"

    async with uow.begin(tenant_id):
        loaded = await repo.get(user.id)
        loaded.rename("Ann Lee")
        await repo.update(loaded)

    async with uow.begin(tenant_id):
        again = await repo.get(user.id)
        assert again.full_name == "Ann Lee"


async def test_get_by_email_and_missing(container, tenant_id):
    repo = container.users.user_repository()
    uow = container.shared.unit_of_work()
    user = User.register(tenant_id=TenantId(tenant_id), email=Email("x@y.com"), full_name="Ex")
    async with uow.begin(tenant_id):
        await repo.add(user)
    async with uow.begin(tenant_id):
        assert (await repo.get_by_email(Email("x@y.com"))) is not None
        assert (await repo.get_by_email(Email("none@y.com"))) is None
        assert (await repo.get(UserId.generate())) is None


async def test_list_users(container, tenant_id):
    repo = container.users.user_repository()
    uow = container.shared.unit_of_work()
    async with uow.begin(tenant_id):
        for i in range(3):
            await repo.add(
                User.register(
                    tenant_id=TenantId(tenant_id),
                    email=Email(f"u{i}@y.com"),
                    full_name=f"U{i}",
                )
            )
    async with uow.begin(tenant_id):
        assert len(await repo.list()) == 3
