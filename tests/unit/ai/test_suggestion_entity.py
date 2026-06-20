from __future__ import annotations

import pytest

from todo_app.contexts.ai.domain.entities.ai_suggestion import (
    AiSuggestion,
    SuggestionStatus,
)
from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId


def _request() -> AiSuggestion:
    return AiSuggestion.request(
        tenant_id=TenantId.generate(),
        prompt=PromptText("hello"),
        model=ModelIdentifier("m"),
    )


def test_request_starts_pending():
    assert _request().status is SuggestionStatus.PENDING


def test_complete_sets_response():
    s = _request()
    s.complete("answer")
    assert s.status is SuggestionStatus.COMPLETED
    assert s.response == "answer"


def test_complete_blank_rejected():
    with pytest.raises(DomainValidationError):
        _request().complete("  ")


def test_fail_records_error():
    s = _request()
    s.fail("boom")
    assert s.status is SuggestionStatus.FAILED
    assert s.error == "boom"


@pytest.mark.parametrize("bad", ["", "   "])
def test_prompt_rejects_empty(bad):
    with pytest.raises(DomainValidationError):
        PromptText(bad)


def test_prompt_rejects_too_long():
    with pytest.raises(DomainValidationError):
        PromptText("x" * 8001)


def test_model_identifier_rejects_empty():
    with pytest.raises(DomainValidationError):
        ModelIdentifier(" ")
