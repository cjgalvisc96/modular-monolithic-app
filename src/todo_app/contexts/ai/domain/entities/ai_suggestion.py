"""AiSuggestion aggregate — models one AI interaction (prompt → response)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from todo_app.contexts.ai.domain.value_objects.suggestion_id import SuggestionId
from todo_app.contexts.shared.domain.entities.aggregate import AggregateRoot
from todo_app.contexts.shared.domain.exceptions import DomainValidationError

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
    from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
    from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId


class SuggestionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(eq=False)
class AiSuggestion(AggregateRoot):
    id: SuggestionId
    tenant_id: TenantId
    prompt: PromptText
    model: ModelIdentifier
    status: SuggestionStatus = SuggestionStatus.PENDING
    response: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        super().__init__()

    @classmethod
    def request(
        cls,
        *,
        tenant_id: TenantId,
        prompt: PromptText,
        model: ModelIdentifier,
        suggestion_id: SuggestionId | None = None,
    ) -> AiSuggestion:
        return cls(
            id=suggestion_id or SuggestionId.generate(),
            tenant_id=tenant_id,
            prompt=prompt,
            model=model,
        )

    def complete(self, response: str) -> None:
        if not response.strip():
            raise DomainValidationError("AI response must not be empty")
        self.response = response
        self.status = SuggestionStatus.COMPLETED

    def fail(self, error: str) -> None:
        self.error = error
        self.status = SuggestionStatus.FAILED
