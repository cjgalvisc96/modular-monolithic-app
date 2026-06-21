"""Authorization role — mirrors the Cognito group claim."""

from enum import StrEnum

from todo_app.contexts.shared.domain.exceptions import DomainValidationError


class Role(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"

    @classmethod
    def parse(cls, raw: str) -> Role:
        try:
            return cls(str(raw).lower())
        except ValueError as exc:
            raise DomainValidationError(f"Unknown role: {raw!r}") from exc

    @property
    def is_admin(self) -> bool:
        return self is Role.ADMIN
