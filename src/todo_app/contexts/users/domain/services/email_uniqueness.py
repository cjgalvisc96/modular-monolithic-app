"""Domain service: email uniqueness is a rule spanning the whole User set,
so it does not belong to a single User entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.exceptions import ConflictError

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.value_objects.email import Email
    from todo_app.contexts.users.domain.repositories.user_repository import UserRepository


class EmailUniquenessChecker:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def ensure_unique(self, email: Email) -> None:
        existing = await self._repository.get_by_email(email)
        if existing is not None:
            raise ConflictError(f"Email already registered: {email}")
