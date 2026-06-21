"""FastAPI background-task definitions; each runs in its own tenant-scoped Unit of Work."""

import logging
from typing import TYPE_CHECKING

from todo_app.contexts.ai.application.dto.suggestion_dto import GenerateSuggestionInput
from todo_app.contexts.shared.application.request_context import (
    RequestContext,
    bind_context,
)

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.core.di.container import ApplicationContainer

logger = logging.getLogger("todo_app.background")


async def generate_suggestion_in_background(
    container: ApplicationContainer, ctx: RequestContext, owner_id: UUID, instruction: str
) -> None:
    """Async AI suggestion generation dispatched off the request path."""
    command = container.ai.generate_suggestion_command()
    uow = container.shared.unit_of_work()
    with bind_context(ctx):
        async with uow.begin(ctx.tenant_id):
            try:
                await command.execute(
                    ctx.tenant_id,
                    GenerateSuggestionInput(owner_id=owner_id, instruction=instruction),
                )
            except Exception:
                logger.exception("background suggestion generation failed")


async def notify(message: str) -> None:
    """Placeholder notification dispatch (e.g. email/SNS in the cloud)."""
    logger.info("notification: %s", message)
