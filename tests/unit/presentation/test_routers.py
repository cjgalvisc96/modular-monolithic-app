"""Router handlers invoked directly with fakes — no app, no client, no DB.

Each handler is a plain async function; its FastAPI ``Depends`` defaults are
supplied explicitly here so the transport logic (use-case call, UoW scope, cache
invalidation, serialization) is exercised in the unit tier.
"""

from types import SimpleNamespace
from uuid import uuid4

from tests.support.api_fakes import FakeCache, FakeCommand, FakeUow, make_container
from todo_app.contexts.ai.application.dto.suggestion_dto import SuggestionOutput
from todo_app.contexts.shared.application.page import Page
from todo_app.contexts.shared.application.request_context import RequestContext
from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput
from todo_app.contexts.users.application.dto.user_dto import UserOutput
from todo_app.presentation.api.v1.ai import routers as ai_routers
from todo_app.presentation.api.v1.ai.serializers import GenerateSuggestionRequest
from todo_app.presentation.api.v1.tasks import routers as task_routers
from todo_app.presentation.api.v1.tasks.serializers import CreateTaskRequest, UpdateTaskRequest
from todo_app.presentation.api.v1.users import routers as user_routers
from todo_app.presentation.api.v1.users.serializers import ChangeRoleRequest, RegisterUserRequest


def _ctx() -> RequestContext:
    return RequestContext(tenant_id=uuid4(), user_id=uuid4(), roles=frozenset({"admin", "member"}))


def _task_output(tenant_id, **over) -> TaskOutput:
    base = {
        "id": uuid4(),
        "tenant_id": tenant_id,
        "owner_id": uuid4(),
        "title": "T",
        "description": "D",
        "status": "pending",
        "due_date": None,
    }
    base.update(over)
    return TaskOutput(**base)


def _user_output(tenant_id, **over) -> UserOutput:
    base = {
        "id": uuid4(),
        "tenant_id": tenant_id,
        "email": "u@acme.example.com",
        "full_name": "U",
        "role": "member",
        "is_active": True,
    }
    base.update(over)
    return UserOutput(**base)


def _suggestion_output(tenant_id, **over) -> SuggestionOutput:
    base = {
        "id": uuid4(),
        "tenant_id": tenant_id,
        "status": "completed",
        "prompt": "p",
        "response": "r",
        "error": None,
    }
    base.update(over)
    return SuggestionOutput(**base)


# --- tasks -----------------------------------------------------------------
async def test_create_task_executes_command_and_serializes():
    ctx = _ctx()
    uow = FakeUow()
    cmd = FakeCommand(result=_task_output(ctx.tenant_id, title="Ship"))
    container = make_container(tasks={"create_task_command": cmd})
    payload = CreateTaskRequest(owner_id=uuid4(), title="Ship")

    resp = await task_routers.create_task(payload, ctx=ctx, container=container, uow=uow)

    assert resp.title == "Ship"
    assert cmd.calls[0][0][0] == ctx.tenant_id
    assert uow.begin_calls  # scope was opened


async def test_list_tasks_maps_page():
    ctx = _ctx()
    out = _task_output(ctx.tenant_id)
    query = FakeCommand(result=Page(items=[out], total=1, limit=50, offset=0))
    container = make_container(tasks={"list_tasks_query": query})

    resp = await task_routers.list_tasks(
        owner_id=None,
        status_filter="pending",
        limit=50,
        offset=0,
        ctx=ctx,
        container=container,
        uow=FakeUow(),
    )
    assert resp.total == 1
    assert resp.items[0].id == out.id
    assert query.calls[0][1]["status"] == "pending"


async def test_get_task_caches_on_miss():
    ctx = _ctx()
    task_id = uuid4()
    out = _task_output(ctx.tenant_id)
    cache = FakeCache()
    container = make_container(tasks={"get_task_query": FakeCommand(result=out)}, cache=cache)

    resp = await task_routers.get_task(task_id, ctx=ctx, container=container, uow=FakeUow())
    assert resp.id == out.id
    assert ("tasks", f"{ctx.tenant_id}:{task_id}") in cache.store


async def test_update_task_invalidates_cache():
    ctx = _ctx()
    task_id = uuid4()
    cache = FakeCache()
    container = make_container(
        tasks={"update_task_command": FakeCommand(result=_task_output(ctx.tenant_id, title="New"))},
        cache=cache,
    )
    resp = await task_routers.update_task(
        task_id, UpdateTaskRequest(title="New"), ctx=ctx, container=container, uow=FakeUow()
    )
    assert resp.title == "New"
    assert ("tasks", f"{ctx.tenant_id}:{task_id}") in cache.invalidated


async def test_complete_task_invalidates_cache():
    ctx = _ctx()
    task_id = uuid4()
    cache = FakeCache()
    container = make_container(
        tasks={
            "complete_task_command": FakeCommand(
                result=_task_output(ctx.tenant_id, status="completed")
            )
        },
        cache=cache,
    )
    resp = await task_routers.complete_task(task_id, ctx=ctx, container=container, uow=FakeUow())
    assert resp.status == "completed"
    assert ("tasks", f"{ctx.tenant_id}:{task_id}") in cache.invalidated


# --- users -----------------------------------------------------------------
async def test_register_user_executes_command():
    ctx = _ctx()
    container = make_container(
        users={"register_user_command": FakeCommand(result=_user_output(ctx.tenant_id))}
    )
    payload = RegisterUserRequest(email="u@acme.example.com", full_name="U", role="admin")
    resp = await user_routers.register_user(payload, ctx=ctx, container=container, uow=FakeUow())
    assert resp.email == "u@acme.example.com"


async def test_list_users_maps_page():
    ctx = _ctx()
    out = _user_output(ctx.tenant_id)
    container = make_container(
        users={
            "list_users_query": FakeCommand(result=Page(items=[out], total=3, limit=50, offset=0))
        }
    )
    resp = await user_routers.list_users(
        limit=50, offset=0, ctx=ctx, container=container, uow=FakeUow()
    )
    assert resp.total == 3
    assert resp.items[0].email == out.email


async def test_get_user_caches_on_miss():
    ctx = _ctx()
    user_id = uuid4()
    out = _user_output(ctx.tenant_id)
    cache = FakeCache()
    container = make_container(users={"get_user_query": FakeCommand(result=out)}, cache=cache)
    resp = await user_routers.get_user(user_id, ctx=ctx, container=container, uow=FakeUow())
    assert resp.id == out.id
    assert ("users", f"{ctx.tenant_id}:{user_id}") in cache.store


async def test_change_role_invalidates_cache():
    ctx = _ctx()
    user_id = uuid4()
    cache = FakeCache()
    container = make_container(
        users={
            "change_user_role_command": FakeCommand(
                result=_user_output(ctx.tenant_id, role="admin")
            )
        },
        cache=cache,
    )
    resp = await user_routers.change_role(
        user_id, ChangeRoleRequest(role="admin"), ctx=ctx, container=container, uow=FakeUow()
    )
    assert resp.role == "admin"
    assert ("users", f"{ctx.tenant_id}:{user_id}") in cache.invalidated


# --- ai --------------------------------------------------------------------
async def test_generate_suggestion_inline():
    ctx = _ctx()
    container = make_container(
        ai={"generate_suggestion_command": FakeCommand(result=_suggestion_output(ctx.tenant_id))}
    )
    payload = GenerateSuggestionRequest(owner_id=uuid4())
    bg = SimpleNamespace(add_task=lambda *a, **k: None)
    resp = await ai_routers.generate_suggestion(
        payload, background_tasks=bg, ctx=ctx, container=container, uow=FakeUow()
    )
    assert resp is not None
    assert resp.status == "completed"


async def test_generate_suggestion_background_dispatches_and_returns_none():
    ctx = _ctx()
    scheduled: list = []
    bg = SimpleNamespace(add_task=lambda *a, **k: scheduled.append((a, k)))
    container = make_container(ai={})
    payload = GenerateSuggestionRequest(owner_id=uuid4(), background=True)
    resp = await ai_routers.generate_suggestion(
        payload, background_tasks=bg, ctx=ctx, container=container, uow=FakeUow()
    )
    assert resp is None
    assert len(scheduled) == 1


async def test_list_suggestions_maps_page():
    ctx = _ctx()
    out = _suggestion_output(ctx.tenant_id)
    container = make_container(
        ai={
            "list_suggestions_query": FakeCommand(
                result=Page(items=[out], total=1, limit=50, offset=0)
            )
        }
    )
    resp = await ai_routers.list_suggestions(
        limit=50, offset=0, ctx=ctx, container=container, uow=FakeUow()
    )
    assert resp.total == 1
    assert resp.items[0].id == out.id
