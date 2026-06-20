"""RegisterUser use case (write side).

Depends only on domain ports (repository, uniqueness service, event publisher)
injected via the constructor — fully unit-testable with in-memory fakes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.users.application.dto.user_dto import RegisterUserInput, UserOutput
from todo_app.contexts.users.domain.entities.user import User
from todo_app.contexts.users.domain.value_objects.role import Role

if TYPE_CHECKING:
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
    ) -> None:
        self._repository = repository
        self._uniqueness = uniqueness
        self._publisher = publisher

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
        return UserOutput.from_entity(user)
