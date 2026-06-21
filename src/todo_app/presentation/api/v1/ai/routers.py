from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

from todo_app.contexts.shared.application.request_context import RequestContext
from todo_app.presentation.api import tasks as background
from todo_app.presentation.api.dependencies import get_container, get_request_context
from todo_app.presentation.api.pagination import PageResponse
from todo_app.presentation.api.runtime import get_uow
from todo_app.presentation.api.v1.ai.serializers import (
    GenerateSuggestionRequest,
    SuggestionResponse,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/suggestions", response_model=SuggestionResponse | None)
async def generate_suggestion(
    payload: GenerateSuggestionRequest,
    background_tasks: BackgroundTasks,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
):
    """Generate an AI task suggestion.

    Inline by default; pass ``background=true`` to dispatch it as a fire-and-
    forget background task (returns 202 with no body).
    """
    if payload.background:
        background_tasks.add_task(
            background.generate_suggestion_in_background,
            container,
            ctx,
            payload.owner_id,
            payload.instruction,
        )
        return None

    command = container.ai.generate_suggestion_command()
    async with uow.begin():
        result = await command.execute(ctx.tenant_id, payload.to_input())
    return SuggestionResponse.from_output(result)


@router.get("/suggestions", response_model=PageResponse[SuggestionResponse])
async def list_suggestions(
    limit: int = 50,
    offset: int = 0,
    ctx: RequestContext = Depends(get_request_context),
    container=Depends(get_container),
    uow=Depends(get_uow),
) -> PageResponse[SuggestionResponse]:
    query = container.ai.list_suggestions_query()
    async with uow.begin():
        page = await query.execute(limit=limit, offset=offset)
    return PageResponse.from_page(page, SuggestionResponse.from_output)
