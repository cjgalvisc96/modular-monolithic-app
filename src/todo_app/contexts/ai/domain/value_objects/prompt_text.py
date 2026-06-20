from __future__ import annotations

from dataclasses import dataclass

from todo_app.contexts.shared.domain.exceptions import DomainValidationError

_MAX_PROMPT_CHARS = 8000


@dataclass(frozen=True, slots=True)
class PromptText:
    value: str

    def __post_init__(self) -> None:
        text = self.value.strip()
        if not text:
            raise DomainValidationError("Prompt must not be empty")
        if len(text) > _MAX_PROMPT_CHARS:
            raise DomainValidationError(f"Prompt exceeds {_MAX_PROMPT_CHARS} characters")
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value
