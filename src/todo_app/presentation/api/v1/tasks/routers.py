from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from todo_app.contexts.shared.application.request_context import RequestContext
from todo_app.presentation.api.caching import cached
from todo_app.presentation.api.dependencies import get_container, get_request_context
from todo_app.presentation.api.pagination import PageResponse
from todo_app.presentation.api.runtime import get_uow
from todo_app.presentation.api.v1.tasks.serializers import (
    CreateTaskRequest,
    TaskResponse,
    UpdateTaskRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: CreateTaskRequest,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> TaskResponse:
    command = container.tasks.create_task_command()
    async with uow.begin():
        result = await command.execute(ctx.tenant_id, payload.to_input())
    return TaskResponse.from_output(result)


@router.get("", response_model=PageResponse[TaskResponse])
async def list_tasks(
    owner_id: UUID | None = None,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> PageResponse[TaskResponse]:
    query = container.tasks.list_tasks_query()
    async with uow.begin():
        page = await query.execute(
            owner_id=owner_id, status=status_filter, limit=limit, offset=offset
        )
    return PageResponse.from_page(page, TaskResponse.from_output)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> TaskResponse:
    async def produce() -> TaskResponse:
        query = container.tasks.get_task_query()
        async with uow.begin():
            return TaskResponse.from_output(await query.execute(task_id))

    cache = container.shared.cache()
    return await cached(cache, "tasks", f"{ctx.tenant_id}:{task_id}", TaskResponse, produce)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: UpdateTaskRequest,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> TaskResponse:
    command = container.tasks.update_task_command()
    async with uow.begin():
        result = await command.execute(task_id, payload.to_input())
    await container.shared.cache().invalidate("tasks", f"{ctx.tenant_id}:{task_id}")
    return TaskResponse.from_output(result)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> TaskResponse:
    command = container.tasks.complete_task_command()
    async with uow.begin():
        result = await command.execute(task_id)
    await container.shared.cache().invalidate("tasks", f"{ctx.tenant_id}:{task_id}")
    return TaskResponse.from_output(result)
