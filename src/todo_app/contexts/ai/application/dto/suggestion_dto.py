from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.ai.domain.entities.ai_suggestion import AiSuggestion


@dataclass(frozen=True, slots=True)
class GenerateSuggestionInput:
    owner_id: UUID
    instruction: str = "Suggest the next task I should focus on."


@dataclass(frozen=True, slots=True)
class SuggestionOutput:
    id: UUID
    tenant_id: UUID
    status: str
    prompt: str
    response: str | None
    error: str | None

    @classmethod
    def from_entity(cls, suggestion: AiSuggestion) -> SuggestionOutput:
        return cls(
            id=suggestion.id.value,
            tenant_id=suggestion.tenant_id.value,
            status=suggestion.status.value,
            prompt=str(suggestion.prompt),
            response=suggestion.response,
            error=suggestion.error,
        )
