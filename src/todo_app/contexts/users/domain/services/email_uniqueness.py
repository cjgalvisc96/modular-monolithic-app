"""Email uniqueness spans the whole User set, so it is a domain service, not an entity rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.users.domain.exceptions import EmailAlreadyRegisteredError

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.value_objects.email import Email
    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository


class EmailUniquenessChecker:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def ensure_unique(self, email: Email) -> None:
        existing = await self._repository.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyRegisteredError(email)
