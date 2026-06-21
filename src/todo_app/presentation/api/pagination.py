from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from todo_app.contexts.shared.application.page import Page


class PageResponse[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_page(cls, page: Page[Any], mapper: Callable[[Any], T]) -> PageResponse[T]:
        return cls(
            items=[mapper(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )
