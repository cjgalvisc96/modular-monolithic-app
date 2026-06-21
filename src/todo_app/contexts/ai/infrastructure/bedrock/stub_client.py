"""Deterministic local LLM stub for DEBUG runs without Bedrock credentials."""

from typing import TYPE_CHECKING

from todo_app.contexts.ai.domain.ports.llm_client import LlmClient, LlmCompletion

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
    from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText


class StubLlmClient(LlmClient):
    async def complete(self, prompt: PromptText, model: ModelIdentifier) -> LlmCompletion:
        preview = str(prompt).splitlines()[0][:80]
        text = f"[stub:{model}] Based on '{preview}', focus on the highest-priority pending task."
        return LlmCompletion(text=text, model=str(model))
