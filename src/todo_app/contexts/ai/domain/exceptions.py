"""AI-context domain exceptions (subclass the shared kernel base types)."""

from __future__ import annotations

from todo_app.contexts.shared.domain.exceptions import DomainValidationError


class InvalidPromptError(DomainValidationError):
    """The prompt text violates an invariant (empty or too long)."""


class InvalidModelIdentifierError(DomainValidationError):
    """The model identifier was blank."""

    def __init__(self) -> None:
        super().__init__("Model identifier must not be empty")
