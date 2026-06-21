from todo_app.contexts.ai.domain.entities.ai_suggestion import (
    AiSuggestion,
    SuggestionStatus,
)
from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
from todo_app.contexts.ai.domain.value_objects.suggestion_id import SuggestionId
from todo_app.contexts.ai.infrastructure.db.models.suggestion_model import AiSuggestionModel
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId


class SuggestionMapper:
    @staticmethod
    def to_entity(model: AiSuggestionModel) -> AiSuggestion:
        return AiSuggestion(
            id=SuggestionId(model.id),
            tenant_id=TenantId(model.tenant_id),
            prompt=PromptText(model.prompt),
            model=ModelIdentifier(model.model),
            status=SuggestionStatus(model.status),
            response=model.response,
            error=model.error,
        )

    @staticmethod
    def to_model(entity: AiSuggestion) -> AiSuggestionModel:
        return AiSuggestionModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            prompt=str(entity.prompt),
            model=str(entity.model),
            status=entity.status.value,
            response=entity.response,
            error=entity.error,
        )

    @staticmethod
    def apply(entity: AiSuggestion, model: AiSuggestionModel) -> None:
        model.status = entity.status.value
        model.response = entity.response
        model.error = entity.error
