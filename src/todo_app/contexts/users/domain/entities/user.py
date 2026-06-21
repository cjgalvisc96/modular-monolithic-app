from dataclasses import dataclass
from typing import TYPE_CHECKING

from todo_app.contexts.shared.domain.entities.aggregate import AggregateRoot
from todo_app.contexts.shared.domain.exceptions import DomainValidationError
from todo_app.contexts.users.domain.events import UserRegistered
from todo_app.contexts.users.domain.value_objects.role import Role
from todo_app.contexts.users.domain.value_objects.user_id import UserId

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.value_objects.email import Email
    from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId


@dataclass(eq=False)
class User(AggregateRoot):
    """A user belonging to exactly one tenant."""

    id: UserId
    tenant_id: TenantId
    email: Email
    full_name: str
    role: Role = Role.MEMBER
    is_active: bool = True

    def __post_init__(self) -> None:
        super().__init__()
        if not self.full_name.strip():
            raise DomainValidationError("User full_name must not be empty")

    @classmethod
    def register(
        cls,
        *,
        tenant_id: TenantId,
        email: Email,
        full_name: str,
        role: Role = Role.MEMBER,
        user_id: UserId | None = None,
    ) -> User:
        user = cls(
            id=user_id or UserId.generate(),
            tenant_id=tenant_id,
            email=email,
            full_name=full_name.strip(),
            role=role,
        )
        user.record_event(
            UserRegistered(
                tenant_id=tenant_id.value,
                user_id=user.id.value,
                email=str(email),
            )
        )
        return user

    def rename(self, full_name: str) -> None:
        if not full_name.strip():
            raise DomainValidationError("User full_name must not be empty")
        self.full_name = full_name.strip()

    def change_role(self, role: Role) -> None:
        self.role = role

    def deactivate(self) -> None:
        self.is_active = False
