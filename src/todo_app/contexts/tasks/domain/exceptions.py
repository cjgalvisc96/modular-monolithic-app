"""Tasks-context domain exceptions.

Context-specific errors that subclass the shared kernel's base types, so the
presentation layer keeps mapping them to the right HTTP status while the message
and meaning are specific to this context.
"""

from __future__ import annotations

from todo_app.contexts.shared.domain.exceptions import (
    DomainValidationError,
    EntityNotFoundError,
)


class TaskNotFoundError(EntityNotFoundError):
    """No task with the given id exists in the current tenant scope."""

    def __init__(self, identifier: object) -> None:
        super().__init__("Task", identifier)


class EmptyTaskTitleError(DomainValidationError):
    """A task title was blank."""

    def __init__(self) -> None:
        super().__init__("Task title must not be empty")
