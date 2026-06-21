"""Persistence port for AiSuggestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.entities.ai_suggestion import AiSuggestion
    from todo_app.contexts.ai.domain.value_objects.suggestion_id import SuggestionId


class SuggestionRepository(ABC):
    @abstractmethod
    async def add(self, suggestion: AiSuggestion) -> None: ...

    @abstractmethod
    async def get(self, suggestion_id: SuggestionId) -> AiSuggestion | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 50, offset: int = 0) -> list[AiSuggestion]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def update(self, suggestion: AiSuggestion) -> None: ...
