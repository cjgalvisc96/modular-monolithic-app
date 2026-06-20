from __future__ import annotations

from dataclasses import dataclass

from todo_app.contexts.shared.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class ModelIdentifier:
    """An opaque model id (e.g. a Bedrock model id). The domain stays unaware
    that this happens to name an AWS resource."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise DomainValidationError("Model identifier must not be empty")

    def __str__(self) -> str:
        return self.value
