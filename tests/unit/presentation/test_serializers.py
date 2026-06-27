"""Serializer mapping is pure (domain/DTO <-> HTTP), so it unit-tests directly."""

from datetime import date
from uuid import uuid4

from todo_app.contexts.ai.application.dto.suggestion_dto import SuggestionOutput
from todo_app.contexts.tasks.application.dto.task_dto import TaskOutput
from todo_app.contexts.users.application.dto.user_dto import UserOutput
from todo_app.presentation.api.v1.ai.serializers import (
    GenerateSuggestionRequest,
    SuggestionResponse,
)
from todo_app.presentation.api.v1.tasks.serializers import (
    CreateTaskRequest,
    TaskResponse,
    UpdateTaskRequest,
)
from todo_app.presentation.api.v1.users.serializers import (
    RegisterUserRequest,
    UserResponse,
)


def test_create_task_request_to_input():
    owner = uuid4()
    due = date(2030, 1, 2)
    payload = CreateTaskRequest(owner_id=owner, title="Ship", description="d", due_date=due)
    inp = payload.to_input()
    assert inp.owner_id == owner
    assert inp.title == "Ship"
    assert inp.description == "d"
    assert inp.due_date == due


def test_update_task_request_to_input_defaults_to_none():
    inp = UpdateTaskRequest().to_input()
    assert inp.title is None
    assert inp.description is None
    assert inp.due_date is None


def test_task_response_from_output():
    out = TaskOutput(
        id=uuid4(),
        tenant_id=uuid4(),
        owner_id=uuid4(),
        title="T",
        description="D",
        status="pending",
        due_date=None,
    )
    resp = TaskResponse.from_output(out)
    assert resp.id == out.id
    assert resp.tenant_id == out.tenant_id
    assert resp.owner_id == out.owner_id
    assert resp.status == "pending"


def test_register_user_request_to_input_stringifies_email():
    payload = RegisterUserRequest(email="a@acme.example.com", full_name="A", role="admin")
    inp = payload.to_input()
    assert inp.email == "a@acme.example.com"
    assert inp.full_name == "A"
    assert inp.role == "admin"


def test_register_user_request_defaults_to_member():
    payload = RegisterUserRequest(email="b@acme.example.com", full_name="B")
    assert payload.to_input().role == "member"


def test_user_response_from_output():
    out = UserOutput(
        id=uuid4(),
        tenant_id=uuid4(),
        email="u@acme.example.com",
        full_name="U",
        role="member",
        is_active=True,
    )
    resp = UserResponse.from_output(out)
    assert resp.email == "u@acme.example.com"
    assert resp.is_active is True


def test_generate_suggestion_request_to_input_drops_background_flag():
    owner = uuid4()
    payload = GenerateSuggestionRequest(owner_id=owner, instruction="Do X", background=True)
    inp = payload.to_input()
    assert inp.owner_id == owner
    assert inp.instruction == "Do X"
    assert not hasattr(inp, "background")


def test_suggestion_response_from_output():
    out = SuggestionOutput(
        id=uuid4(),
        tenant_id=uuid4(),
        status="completed",
        prompt="p",
        response="r",
        error=None,
    )
    resp = SuggestionResponse.from_output(out)
    assert resp.status == "completed"
    assert resp.response == "r"
    assert resp.error is None
