"""Email value object with light, framework-free validation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from todo_app.contexts.shared.domain.exceptions import DomainValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise DomainValidationError(f"Invalid email address: {self.value!r}")
        # frozen dataclass — bypass to store the normalized form
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
