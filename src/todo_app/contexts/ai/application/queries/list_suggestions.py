from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.ai.application.dto.suggestion_dto import SuggestionOutput

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.repositories.suggestion_repository import (
        SuggestionRepository,
    )


class ListSuggestionsQuery:
    def __init__(self, repository: SuggestionRepository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int = 50, offset: int = 0) -> list[SuggestionOutput]:
        suggestions = await self._repository.list(limit=limit, offset=offset)
        return [SuggestionOutput.from_entity(s) for s in suggestions]
