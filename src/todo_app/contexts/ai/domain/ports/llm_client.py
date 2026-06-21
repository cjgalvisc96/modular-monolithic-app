"""LLM client port; the domain has no awareness the implementation is AWS Bedrock."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
    from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText


@dataclass(frozen=True, slots=True)
class LlmCompletion:
    text: str
    model: str


class LlmClient(ABC):
    @abstractmethod
    async def complete(self, prompt: PromptText, model: ModelIdentifier) -> LlmCompletion:
        """Run a single prompt against the model and return its completion."""
