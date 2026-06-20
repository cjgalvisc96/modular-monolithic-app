from __future__ import annotations

import pytest

from todo_app.contexts.shared.application.request_context import RequestContext
from todo_app.presentation.api import tasks as background

pytestmark = pytest.mark.asyncio


async def test_generate_suggestion_in_background_persists(container, tenant_id):
    ctx = RequestContext(tenant_id=tenant_id, user_id=None, roles=frozenset({"member"}))
    from uuid import uuid4

    await background.generate_suggestion_in_background(container, ctx, uuid4(), "Suggest something")
    uow = container.shared.unit_of_work()
    async with uow.begin(tenant_id):
        stored = await container.ai.suggestion_repository().list()
    assert len(stored) == 1
    assert stored[0].status.value == "completed"


async def test_generate_suggestion_in_background_swallows_errors(container, tenant_id):
    # Force the LLM to fail; the background task must log and not raise.
    from todo_app.contexts.ai.domain.ports.llm_client import LlmClient

    class _Boom(LlmClient):
        async def complete(self, prompt, model):
            raise RuntimeError("bedrock down")

    container.ai.llm_client.override(_Boom())
    ctx = RequestContext(tenant_id=tenant_id, user_id=None, roles=frozenset({"member"}))
    from uuid import uuid4

    await background.generate_suggestion_in_background(container, ctx, uuid4(), "go")
    container.ai.llm_client.reset_override()


async def test_notify_runs():
    await background.notify("hello")
