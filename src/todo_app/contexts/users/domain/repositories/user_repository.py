"""UserRepository port — interface only, implemented in infrastructure."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.value_objects.email import Email
    from todo_app.contexts.users.domain.entities.user import User
    from todo_app.contexts.users.domain.value_objects.user_id import UserId


class UserRepository(ABC):
    """Persistence boundary for the User aggregate.

    Implementations are tenant-scoped by RLS; methods never accept a tenant_id
    argument because the active DB session already carries it.
    """

    @abstractmethod
    async def add(self, user: User) -> None: ...

    @abstractmethod
    async def get(self, user_id: UserId) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: Email) -> User | None: ...

    @abstractmethod
    async def list(self, *, limit: int = 50, offset: int = 0) -> list[User]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def update(self, user: User) -> None: ...
