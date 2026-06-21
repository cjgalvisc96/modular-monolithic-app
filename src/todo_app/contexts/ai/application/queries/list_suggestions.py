from typing import TYPE_CHECKING

from todo_app.contexts.ai.application.dto.suggestion_dto import SuggestionOutput
from todo_app.contexts.shared.application.page import Page

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.repositories.suggestion_repository import (
        SuggestionRepository,
    )


class ListSuggestionsQuery:
    def __init__(self, repository: SuggestionRepository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int = 50, offset: int = 0) -> Page[SuggestionOutput]:
        suggestions = await self._repository.list(limit=limit, offset=offset)
        total = await self._repository.count()
        items = [SuggestionOutput.from_entity(s) for s in suggestions]
        return Page(items=items, total=total, limit=limit, offset=offset)
