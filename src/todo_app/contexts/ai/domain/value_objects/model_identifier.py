from __future__ import annotations

from dataclasses import dataclass

from todo_app.contexts.ai.domain.exceptions import InvalidModelIdentifierError


@dataclass(frozen=True, slots=True)
class ModelIdentifier:
    """An opaque model id; the domain stays unaware it names an AWS resource."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise InvalidModelIdentifierError()

    def __str__(self) -> str:
        return self.value
