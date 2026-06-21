"""Tasks-context domain exceptions."""

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
    def __init__(self) -> None:
        super().__init__("Task title must not be empty")
