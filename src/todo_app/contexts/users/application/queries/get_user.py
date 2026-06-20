from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.exceptions import EntityNotFoundError
from todo_app.contexts.users.application.dto.user_dto import UserOutput
from todo_app.contexts.users.domain.value_objects.user_id import UserId

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository


class GetUserByIdQuery:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UUID) -> UserOutput:
        user = await self._repository.get(UserId(user_id))
        if user is None:
            raise EntityNotFoundError("User", user_id)
        return UserOutput.from_entity(user)
