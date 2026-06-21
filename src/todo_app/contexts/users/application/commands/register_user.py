from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.users.application.dto.user_dto import RegisterUserInput, UserOutput
from todo_app.contexts.users.domain.entities.user import User
from todo_app.contexts.users.domain.value_objects.role import Role
from todo_app.core.logging import get_logger

if TYPE_CHECKING:
    from logging import Logger
    from uuid import UUID

    from todo_app.contexts.shared.domain.events.publisher import EventPublisher
    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository
    from todo_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker


class RegisterUserCommand:
    def __init__(
        self,
        repository: UserRepository,
        uniqueness: EmailUniquenessChecker,
        publisher: EventPublisher,
        logger: Logger | None = None,
    ) -> None:
        self._repository = repository
        self._uniqueness = uniqueness
        self._publisher = publisher
        self._logger = logger or get_logger(__name__)

    async def execute(self, tenant_id: UUID, data: RegisterUserInput) -> UserOutput:
        email = Email(data.email)
        await self._uniqueness.ensure_unique(email)
        user = User.register(
            tenant_id=TenantId(tenant_id),
            email=email,
            full_name=data.full_name,
            role=Role.parse(data.role),
        )
        await self._repository.add(user)
        await self._publisher.publish_all(user.pull_events())
        self._logger.info(
            "user.registered",
            extra={"tenant_id": str(tenant_id), "user_id": str(user.id.value)},
        )
        return UserOutput.from_entity(user)
