from enum import StrEnum

from todo_app.contexts.shared.domain.exceptions import DomainValidationError


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    @classmethod
    def parse(cls, raw: str) -> TaskStatus:
        try:
            return cls(str(raw).lower())
        except ValueError as exc:
            raise DomainValidationError(f"Unknown task status: {raw!r}") from exc
