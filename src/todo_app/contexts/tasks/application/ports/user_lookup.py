"""Consumer-defined port owned by `tasks`; `users` provides the adapter at the root."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserSummary:
    id: UUID
    full_name: str
    is_active: bool


class UserLookupPort(ABC):
    @abstractmethod
    async def find(self, user_id: UUID) -> UserSummary | None: ...
