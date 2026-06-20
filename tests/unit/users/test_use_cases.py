from __future__ import annotations

from uuid import uuid4

import pytest

from tests.support.fakes import FakeEventPublisher, FakeUserRepository
from todo_app.contexts.shared.domain.exceptions import ConflictError, EntityNotFoundError
from todo_app.contexts.users.application.commands.change_user_role import (
    ChangeUserRoleCommand,
)
from todo_app.contexts.users.application.commands.register_user import RegisterUserCommand
from todo_app.contexts.users.application.dto.user_dto import RegisterUserInput
from todo_app.contexts.users.application.queries.get_user import GetUserByIdQuery
from todo_app.contexts.users.application.queries.list_users import ListUsersQuery
from todo_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repo():
    return FakeUserRepository()


@pytest.fixture
def publisher():
    return FakeEventPublisher()


@pytest.fixture
def register(repo, publisher):
    return RegisterUserCommand(repo, EmailUniquenessChecker(repo), publisher)


async def test_register_user_persists_and_publishes(register, repo, publisher, tenant_id):
    out = await register.execute(tenant_id, RegisterUserInput("a@b.com", "Ann", "admin"))
    assert out.email == "a@b.com"
    assert out.role == "admin"
    assert len(await repo.list()) == 1
    assert [e.name for e in publisher.published] == ["UserRegistered"]


async def test_register_duplicate_email_conflicts(register, tenant_id):
    await register.execute(tenant_id, RegisterUserInput("dup@b.com", "A"))
    with pytest.raises(ConflictError):
        await register.execute(tenant_id, RegisterUserInput("dup@b.com", "B"))


async def test_get_user_by_id(register, repo, tenant_id):
    out = await register.execute(tenant_id, RegisterUserInput("c@b.com", "Cy"))
    fetched = await GetUserByIdQuery(repo).execute(out.id)
    assert fetched.id == out.id


async def test_get_missing_user_raises(repo):
    with pytest.raises(EntityNotFoundError):
        await GetUserByIdQuery(repo).execute(uuid4())


async def test_change_role(register, repo, tenant_id):
    out = await register.execute(tenant_id, RegisterUserInput("d@b.com", "Di"))
    changed = await ChangeUserRoleCommand(repo).execute(out.id, "admin")
    assert changed.role == "admin"


async def test_change_role_missing_user(repo):
    with pytest.raises(EntityNotFoundError):
        await ChangeUserRoleCommand(repo).execute(uuid4(), "admin")


async def test_list_users(register, repo, tenant_id):
    await register.execute(tenant_id, RegisterUserInput("e@b.com", "Ed"))
    await register.execute(tenant_id, RegisterUserInput("f@b.com", "Fi"))
    listed = await ListUsersQuery(repo).execute()
    assert len(listed) == 2
