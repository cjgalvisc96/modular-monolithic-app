"""Pagination mapping and the get_uow runtime helper — both pure unit."""

from types import SimpleNamespace
from uuid import uuid4

from todo_app.contexts.shared.application.page import Page
from todo_app.contexts.users.application.dto.user_dto import UserOutput
from todo_app.presentation.api.pagination import PageResponse
from todo_app.presentation.api.runtime import get_uow
from todo_app.presentation.api.v1.users.serializers import UserResponse


def test_page_response_from_page_maps_items_and_meta():
    out = UserOutput(
        id=uuid4(),
        tenant_id=uuid4(),
        email="u@acme.example.com",
        full_name="U",
        role="member",
        is_active=True,
    )
    page = Page(items=[out], total=7, limit=50, offset=0)
    resp = PageResponse.from_page(page, UserResponse.from_output)
    assert resp.total == 7
    assert resp.limit == 50
    assert resp.offset == 0
    assert len(resp.items) == 1
    assert resp.items[0].email == "u@acme.example.com"


def test_get_uow_pulls_from_container():
    sentinel = object()
    container = SimpleNamespace(shared=SimpleNamespace(unit_of_work=lambda: sentinel))
    request = SimpleNamespace()
    assert get_uow(request, container) is sentinel
