"""Auth/tenant-resolution dependencies, invoked directly (no FastAPI request cycle)."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from todo_app.contexts.shared.application.request_context import RequestContext
from todo_app.contexts.shared.domain.exceptions import AuthenticationError
from todo_app.presentation.api.dependencies import (
    _bearer_token,
    get_container,
    get_request_context,
    get_settings_dep,
    require_role,
)


def test_get_container_and_settings_read_app_state():
    container = object()
    settings = object()
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(container=container, settings=settings))
    )
    assert get_container(request) is container
    assert get_settings_dep(request) is settings


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("", None),
        ("Bearer abc.def", "abc.def"),
        ("bearer abc.def", "abc.def"),
        ("Basic abc", None),
        ("Bearer ", None),
    ],
)
def test_bearer_token_parsing(header, expected):
    assert _bearer_token(header) == expected


def _claims(tenant_id):
    return SimpleNamespace(tenant_id=tenant_id, subject=uuid4(), roles=frozenset({"admin"}))


def _container_with_auth(authenticator):
    return SimpleNamespace(users=SimpleNamespace(cognito_authenticator=lambda: authenticator))


async def _resolve(**kwargs):
    agen = get_request_context(**kwargs)
    try:
        return await agen.__anext__()
    finally:
        await agen.aclose()


async def test_bearer_token_path_binds_verified_claims():
    tid = uuid4()

    class _Auth:
        async def verify(self, token):
            assert token == "good.token"
            return _claims(tid)

    ctx = await _resolve(
        request=SimpleNamespace(),
        authorization="Bearer good.token",
        x_dev_tenant=None,
        x_dev_roles=None,
        container=_container_with_auth(_Auth()),
        settings=SimpleNamespace(debug=False),
    )
    assert ctx.tenant_id == tid
    assert ctx.has_role("admin")


async def test_invalid_bearer_token_raises_401():
    class _Auth:
        async def verify(self, token):
            raise AuthenticationError("expired")

    with pytest.raises(HTTPException) as ei:
        await _resolve(
            request=SimpleNamespace(),
            authorization="Bearer bad",
            x_dev_tenant=None,
            x_dev_roles=None,
            container=_container_with_auth(_Auth()),
            settings=SimpleNamespace(debug=False),
        )
    assert ei.value.status_code == 401


async def test_debug_dev_header_path_builds_context():
    tid = uuid4()
    ctx = await _resolve(
        request=SimpleNamespace(),
        authorization=None,
        x_dev_tenant=str(tid),
        x_dev_roles="admin, member",
        container=SimpleNamespace(),
        settings=SimpleNamespace(debug=True),
    )
    assert ctx.tenant_id == tid
    assert ctx.has_role("admin")
    assert ctx.has_role("member")


async def test_dev_header_without_roles_defaults_to_member():
    ctx = await _resolve(
        request=SimpleNamespace(),
        authorization=None,
        x_dev_tenant=str(uuid4()),
        x_dev_roles=None,
        container=SimpleNamespace(),
        settings=SimpleNamespace(debug=True),
    )
    assert ctx.has_role("member")


async def test_no_credentials_raises_401():
    with pytest.raises(HTTPException) as ei:
        await _resolve(
            request=SimpleNamespace(),
            authorization=None,
            x_dev_tenant=None,
            x_dev_roles=None,
            container=SimpleNamespace(),
            settings=SimpleNamespace(debug=True),
        )
    assert ei.value.status_code == 401


def test_require_role_allows_and_denies():
    checker = require_role("admin")
    admin = RequestContext(tenant_id=uuid4(), roles=frozenset({"admin"}))
    assert checker(admin) is admin

    member = RequestContext(tenant_id=uuid4(), roles=frozenset({"member"}))
    with pytest.raises(HTTPException) as ei:
        checker(member)
    assert ei.value.status_code == 403
