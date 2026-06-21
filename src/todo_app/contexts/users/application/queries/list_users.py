from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.application.page import Page
from todo_app.contexts.users.application.dto.user_dto import UserOutput

if TYPE_CHECKING:
    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository


class ListUsersQuery:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, *, limit: int = 50, offset: int = 0) -> Page[UserOutput]:
        users = await self._repository.list(limit=limit, offset=offset)
        total = await self._repository.count()
        items = [UserOutput.from_entity(u) for u in users]
        return Page(items=items, total=total, limit=limit, offset=offset)
