from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    total: int
    limit: int
    offset: int
