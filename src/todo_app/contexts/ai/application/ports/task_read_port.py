"""Consumer-defined port: read-only task context the AI needs to build a prompt.

`ai` owns this interface; `tasks`' read side satisfies it via an adapter wired at
the root ApplicationContainer (the same explicit-wiring pattern as tasks→users).
`ai` never imports `tasks` internals.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, slots=True)
class TaskBrief:
    title: str
    status: str


class TaskReadPort(ABC):
    @abstractmethod
    async def list_for_owner(self, owner_id: UUID, *, limit: int = 20) -> list[TaskBrief]: ...
