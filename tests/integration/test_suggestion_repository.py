from __future__ import annotations

import pytest

from todo_app.contexts.ai.domain.entities.ai_suggestion import AiSuggestion
from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId

pytestmark = pytest.mark.asyncio


async def test_persist_and_update_suggestion(container, tenant_id):
    repo = container.ai.suggestion_repository()
    uow = container.shared.unit_of_work()
    suggestion = AiSuggestion.request(
        tenant_id=TenantId(tenant_id),
        prompt=PromptText("hi"),
        model=ModelIdentifier("m"),
    )
    async with uow.begin(tenant_id):
        await repo.add(suggestion)
        suggestion.complete("answer")
        await repo.update(suggestion)

    async with uow.begin(tenant_id):
        listed = await repo.list()
        assert len(listed) == 1
        assert listed[0].response == "answer"
        assert (await repo.get(suggestion.id)).status.value == "completed"
