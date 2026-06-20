"""UUID-backed identifier value object, base for every aggregate id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from todo_app.contexts.shared.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class EntityId:
    """An immutable UUID identity. Subclass per aggregate for type safety."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise DomainValidationError(f"{type(self).__name__} must wrap a UUID")

    @classmethod
    def generate(cls) -> Self:
        return cls(uuid4())

    @classmethod
    def from_string(cls, raw: str) -> Self:
        try:
            return cls(UUID(str(raw)))
        except (ValueError, AttributeError, TypeError) as exc:
            raise DomainValidationError(f"Invalid {cls.__name__}: {raw!r}") from exc

    def __str__(self) -> str:
        return str(self.value)
