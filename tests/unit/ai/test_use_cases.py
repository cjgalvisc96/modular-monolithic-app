import pytest

from tests.support.fakes import FakeLlmClient, FakeSuggestionRepository, FakeTaskRead
from todo_app.contexts.ai.application.commands.generate_task_suggestion import (
    GenerateTaskSuggestionCommand,
)
from todo_app.contexts.ai.application.dto.suggestion_dto import GenerateSuggestionInput
from todo_app.contexts.ai.application.ports.task_read_port import TaskBrief
from todo_app.contexts.ai.application.queries.list_suggestions import ListSuggestionsQuery

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repo():
    return FakeSuggestionRepository()


async def test_generate_uses_task_context_and_persists(repo, tenant_id):
    llm = FakeLlmClient(reply="Focus on A")
    reader = FakeTaskRead([TaskBrief("A", "pending"), TaskBrief("B", "completed")])
    cmd = GenerateTaskSuggestionCommand(repo, llm, reader, "model-x")
    out = await cmd.execute(tenant_id, GenerateSuggestionInput(owner_id=tenant_id))
    assert out.status == "completed"
    assert out.response == "Focus on A"
    # prompt included the current tasks
    assert "A" in llm.calls[0] and "B" in llm.calls[0]
    assert len(await repo.list()) == 1


async def test_generate_with_no_tasks(repo, tenant_id):
    llm = FakeLlmClient()
    cmd = GenerateTaskSuggestionCommand(repo, llm, FakeTaskRead([]), "model-x")
    out = await cmd.execute(tenant_id, GenerateSuggestionInput(owner_id=tenant_id))
    assert "no current tasks" in llm.calls[0]
    assert out.status == "completed"


async def test_generate_failure_marks_failed_and_raises(repo, tenant_id):
    llm = FakeLlmClient(fail=True)
    cmd = GenerateTaskSuggestionCommand(repo, llm, FakeTaskRead([]), "model-x")
    with pytest.raises(RuntimeError):
        await cmd.execute(tenant_id, GenerateSuggestionInput(owner_id=tenant_id))
    stored = await repo.list()
    assert stored[0].status.value == "failed"


async def test_list_suggestions(repo, tenant_id):
    llm = FakeLlmClient()
    cmd = GenerateTaskSuggestionCommand(repo, llm, FakeTaskRead([]), "model-x")
    await cmd.execute(tenant_id, GenerateSuggestionInput(owner_id=tenant_id))
    listed = await ListSuggestionsQuery(repo).execute()
    assert listed.total == 1 and len(listed.items) == 1
