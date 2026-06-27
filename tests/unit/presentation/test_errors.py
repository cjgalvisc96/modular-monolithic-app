"""Exception-handler registration maps domain errors to HTTP status codes."""

import json

import pytest
from fastapi import FastAPI

from todo_app.contexts.shared.domain.exceptions import (
    ConflictError,
    DomainValidationError,
    EntityNotFoundError,
    PermissionDeniedError,
)
from todo_app.presentation.api.errors import register_exception_handlers


def _handler_for(exc_type):
    app = FastAPI()
    register_exception_handlers(app)
    return app.exception_handlers[exc_type]


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (EntityNotFoundError("Task", "abc"), 404),
        (ConflictError("dup"), 409),
        (DomainValidationError("bad"), 422),
        (PermissionDeniedError("nope"), 403),
    ],
)
async def test_domain_errors_map_to_status(exc, expected):
    handler = _handler_for(type(exc))
    response = await handler(None, exc)
    assert response.status_code == expected
    body = json.loads(bytes(response.body))
    assert body["error"] == type(exc).__name__
    assert body["detail"] == str(exc)


async def test_unmapped_exception_falls_back_to_400():
    handler = _handler_for(EntityNotFoundError)
    response = await handler(None, ValueError("boom"))
    assert response.status_code == 400
