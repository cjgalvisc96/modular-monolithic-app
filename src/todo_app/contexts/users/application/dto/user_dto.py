"""Application-boundary DTOs for the users context, distinct from API serializers."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.users.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class RegisterUserInput:
    email: str
    full_name: str
    role: str = "member"


@dataclass(frozen=True, slots=True)
class UserOutput:
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    @classmethod
    def from_entity(cls, user: User) -> UserOutput:
        return cls(
            id=user.id.value,
            tenant_id=user.tenant_id.value,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
        )
