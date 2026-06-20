"""Consumer-defined port: what `tasks` needs to know about a user.

`tasks` owns this interface (it expresses *its* needs); the `users` context
provides an adapter at the root ApplicationContainer. `tasks` never imports
`users` internals — preserving bounded-context isolation.
"""

from __future__ import annotations

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
