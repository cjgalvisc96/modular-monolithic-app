from uuid import UUID

from pydantic import BaseModel

from todo_app.contexts.ai.application.dto.suggestion_dto import (
    GenerateSuggestionInput,
    SuggestionOutput,
)


class GenerateSuggestionRequest(BaseModel):
    owner_id: UUID
    instruction: str = "Suggest the next task I should focus on."
    background: bool = False

    def to_input(self) -> GenerateSuggestionInput:
        return GenerateSuggestionInput(owner_id=self.owner_id, instruction=self.instruction)


class SuggestionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    status: str
    prompt: str
    response: str | None
    error: str | None

    @classmethod
    def from_output(cls, dto: SuggestionOutput) -> SuggestionResponse:
        return cls(
            id=dto.id,
            tenant_id=dto.tenant_id,
            status=dto.status,
            prompt=dto.prompt,
            response=dto.response,
            error=dto.error,
        )
