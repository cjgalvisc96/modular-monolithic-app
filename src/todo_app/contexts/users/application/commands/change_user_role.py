from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.users.application.dto.user_dto import UserOutput
from todo_app.contexts.users.domain.exceptions import UserNotFoundError
from todo_app.contexts.users.domain.value_objects.role import Role
from todo_app.contexts.users.domain.value_objects.user_id import UserId
from todo_app.core.logging import get_logger

if TYPE_CHECKING:
    from logging import Logger
    from uuid import UUID

    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository


class ChangeUserRoleCommand:
    def __init__(self, repository: UserRepository, logger: Logger | None = None) -> None:
        self._repository = repository
        self._logger = logger or get_logger(__name__)

    async def execute(self, user_id: UUID, role: str) -> UserOutput:
        user = await self._repository.get(UserId(user_id))
        if user is None:
            raise UserNotFoundError(user_id)
        user.change_role(Role.parse(role))
        await self._repository.update(user)
        self._logger.info("user.role_changed", extra={"user_id": str(user_id), "role": role})
        return UserOutput.from_entity(user)
