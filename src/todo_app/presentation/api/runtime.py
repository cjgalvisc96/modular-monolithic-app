from __future__ import annotations

from fastapi import Depends, Request

from todo_app.contexts.shared.infrastructure.db.unit_of_work import UnitOfWork
from todo_app.presentation.api.dependencies import get_container


def get_uow(
    request: Request,
    container=Depends(get_container),
) -> UnitOfWork:
    return container.shared.unit_of_work()
