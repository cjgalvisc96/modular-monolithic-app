from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from todo_app.contexts.shared.application.request_context import RequestContext
from todo_app.presentation.api.dependencies import (
    get_container,
    get_request_context,
    require_role,
)
from todo_app.presentation.api.runtime import get_uow
from todo_app.presentation.api.v1.users.serializers import (
    ChangeRoleRequest,
    RegisterUserRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterUserRequest,
    ctx: RequestContext = Depends(require_role("admin")),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> UserResponse:
    command = container.users.register_user_command()
    async with uow.begin():
        result = await command.execute(ctx.tenant_id, payload.to_input())
    return UserResponse.from_output(result)


@router.get("", response_model=list[UserResponse])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> list[UserResponse]:
    query = container.users.list_users_query()
    async with uow.begin():
        results = await query.execute(limit=limit, offset=offset)
    return [UserResponse.from_output(r) for r in results]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> UserResponse:
    query = container.users.get_user_query()
    async with uow.begin():
        result = await query.execute(user_id)
    return UserResponse.from_output(result)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_role(
    user_id: UUID,
    payload: ChangeRoleRequest,
    ctx: RequestContext = Depends(require_role("admin")),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> UserResponse:
    command = container.users.change_user_role_command()
    async with uow.begin():
        result = await command.execute(user_id, payload.role)
    return UserResponse.from_output(result)
