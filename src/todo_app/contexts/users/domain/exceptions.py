"""Users-context domain exceptions (subclass the shared kernel base types)."""

from __future__ import annotations

from todo_app.contexts.shared.domain.exceptions import (
    ConflictError,
    EntityNotFoundError,
)


class UserNotFoundError(EntityNotFoundError):
    """No user with the given id exists in the current tenant scope."""

    def __init__(self, identifier: object) -> None:
        super().__init__("User", identifier)


class EmailAlreadyRegisteredError(ConflictError):
    """A user with the given email already exists in the tenant."""

    def __init__(self, email: object) -> None:
        super().__init__(f"Email already registered: {email}")
