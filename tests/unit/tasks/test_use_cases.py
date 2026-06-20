from __future__ import annotations

from uuid import uuid4

import pytest

from tests.support.fakes import FakeEventPublisher, FakeTaskRepository, FakeUserLookup
from todo_app.contexts.shared.domain.exceptions import (
    DomainValidationError,
    EntityNotFoundError,
)
from todo_app.contexts.tasks.application.commands.complete_task import CompleteTaskCommand
from todo_app.contexts.tasks.application.commands.create_task import CreateTaskCommand
from todo_app.contexts.tasks.application.commands.update_task import UpdateTaskCommand
from todo_app.contexts.tasks.application.dto.task_dto import CreateTaskInput, UpdateTaskInput
from todo_app.contexts.tasks.application.ports.user_lookup import UserSummary
from todo_app.contexts.tasks.application.queries.get_task import GetTaskQuery
from todo_app.contexts.tasks.application.queries.list_tasks import ListTasksQuery

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repo():
    return FakeTaskRepository()


@pytest.fixture
def publisher():
    return FakeEventPublisher()


@pytest.fixture
def owner_id():
    return uuid4()


@pytest.fixture
def lookup(owner_id):
    return FakeUserLookup({owner_id: UserSummary(owner_id, "Ann", True)})


@pytest.fixture
def create(repo, lookup, publisher):
    return CreateTaskCommand(repo, lookup, publisher)


async def test_create_task_validates_owner_and_publishes(create, publisher, tenant_id, owner_id):
    out = await create.execute(tenant_id, CreateTaskInput(owner_id, "Do it"))
    assert out.title == "Do it"
    assert [e.name for e in publisher.published] == ["TaskCreated"]


async def test_create_task_unknown_owner_rejected(create, tenant_id):
    with pytest.raises(DomainValidationError):
        await create.execute(tenant_id, CreateTaskInput(uuid4(), "x"))


async def test_create_task_inactive_owner_rejected(repo, publisher, tenant_id):
    inactive = uuid4()
    lookup = FakeUserLookup({inactive: UserSummary(inactive, "Gone", False)})
    cmd = CreateTaskCommand(repo, lookup, publisher)
    with pytest.raises(DomainValidationError):
        await cmd.execute(tenant_id, CreateTaskInput(inactive, "x"))


async def test_complete_task(create, repo, publisher, tenant_id, owner_id):
    out = await create.execute(tenant_id, CreateTaskInput(owner_id, "Do it"))
    completed = await CompleteTaskCommand(repo, publisher).execute(out.id)
    assert completed.status == "completed"


async def test_complete_missing_task(repo, publisher):
    with pytest.raises(EntityNotFoundError):
        await CompleteTaskCommand(repo, publisher).execute(uuid4())


async def test_update_task(create, repo, tenant_id, owner_id):
    out = await create.execute(tenant_id, CreateTaskInput(owner_id, "Do it"))
    updated = await UpdateTaskCommand(repo).execute(out.id, UpdateTaskInput(title="Renamed"))
    assert updated.title == "Renamed"


async def test_update_missing_task_raises(repo):
    with pytest.raises(EntityNotFoundError):
        await UpdateTaskCommand(repo).execute(uuid4(), UpdateTaskInput(title="x"))


async def test_get_missing_task_raises(repo):
    from todo_app.contexts.tasks.application.queries.get_task import GetTaskQuery

    with pytest.raises(EntityNotFoundError):
        await GetTaskQuery(repo).execute(uuid4())


async def test_get_and_list_tasks(create, repo, tenant_id, owner_id):
    await create.execute(tenant_id, CreateTaskInput(owner_id, "A"))
    out_b = await create.execute(tenant_id, CreateTaskInput(owner_id, "B"))
    got = await GetTaskQuery(repo).execute(out_b.id)
    assert got.title == "B"
    listed = await ListTasksQuery(repo).execute(owner_id=owner_id)
    assert len(listed) == 2


async def test_list_filters_by_status(create, repo, tenant_id, owner_id):
    out = await create.execute(tenant_id, CreateTaskInput(owner_id, "A"))
    await CompleteTaskCommand(repo, FakeEventPublisher()).execute(out.id)
    completed = await ListTasksQuery(repo).execute(status="completed")
    assert len(completed) == 1
