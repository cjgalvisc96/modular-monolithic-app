"""Consumer-defined read-only port; `ai` owns it, `tasks` satisfies it via a root adapter."""

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
