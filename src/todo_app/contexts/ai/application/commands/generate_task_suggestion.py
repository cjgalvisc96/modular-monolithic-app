"""GenerateTaskSuggestion use case."""

from typing import TYPE_CHECKING

from todo_app.contexts.ai.application.dto.suggestion_dto import (
    GenerateSuggestionInput,
    SuggestionOutput,
)
from todo_app.contexts.ai.domain.entities.ai_suggestion import AiSuggestion
from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.core.logging import get_logger

if TYPE_CHECKING:
    from logging import Logger
    from uuid import UUID

    from todo_app.contexts.ai.application.ports.task_read_port import TaskBrief, TaskReadPort
    from todo_app.contexts.ai.domain.ports.llm_client import LlmClient
    from todo_app.contexts.ai.domain.repositories.suggestion_repository import (
        SuggestionRepository,
    )


class GenerateTaskSuggestionCommand:
    def __init__(
        self,
        repository: SuggestionRepository,
        llm_client: LlmClient,
        task_read_port: TaskReadPort,
        model_id: str,
        logger: Logger | None = None,
    ) -> None:
        self._repository = repository
        self._llm = llm_client
        self._tasks = task_read_port
        self._model = ModelIdentifier(model_id)
        self._logger = logger or get_logger(__name__)

    async def execute(self, tenant_id: UUID, data: GenerateSuggestionInput) -> SuggestionOutput:
        briefs = await self._tasks.list_for_owner(data.owner_id)
        prompt = PromptText(self._build_prompt(data.instruction, briefs))
        suggestion = AiSuggestion.request(
            tenant_id=TenantId(tenant_id), prompt=prompt, model=self._model
        )
        await self._repository.add(suggestion)
        try:
            completion = await self._llm.complete(prompt, self._model)
            suggestion.complete(completion.text)
        except Exception as exc:
            suggestion.fail(str(exc))
            await self._repository.update(suggestion)
            raise
        await self._repository.update(suggestion)
        self._logger.info(
            "ai.suggestion_generated",
            extra={"tenant_id": str(tenant_id), "suggestion_id": str(suggestion.id.value)},
        )
        return SuggestionOutput.from_entity(suggestion)

    @staticmethod
    def _build_prompt(instruction: str, briefs: list[TaskBrief]) -> str:
        if briefs:
            listing = "\n".join(f"- [{b.status}] {b.title}" for b in briefs)
        else:
            listing = "(no current tasks)"
        return (
            f"{instruction}\n\nThe user's current tasks are:\n{listing}\n\n"
            "Respond with a single concise, actionable suggestion."
        )
