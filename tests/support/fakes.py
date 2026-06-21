"""In-memory fakes implementing the domain ports.

Unit tests for the application layer use these — no DB, no AWS, no FastAPI.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from todo_app.contexts.ai.application.ports.task_read_port import TaskBrief, TaskReadPort
from todo_app.contexts.ai.domain.ports.llm_client import LlmClient, LlmCompletion
from todo_app.contexts.ai.domain.repositories.suggestion_repository import (
    SuggestionRepository,
)
from todo_app.contexts.tasks.application.ports.user_lookup import UserLookupPort, UserSummary
from todo_app.contexts.tasks.domain.repositories.task_repository import TaskRepository
from todo_app.contexts.users.domain.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    from uuid import UUID

    from todo_app.contexts.ai.domain.entities.ai_suggestion import AiSuggestion
    from todo_app.contexts.ai.domain.value_objects.model_identifier import ModelIdentifier
    from todo_app.contexts.ai.domain.value_objects.prompt_text import PromptText
    from todo_app.contexts.ai.domain.value_objects.suggestion_id import SuggestionId
    from todo_app.contexts.shared.domain.events.base import DomainEvent
    from todo_app.contexts.shared.domain.value_objects.email import Email
    from todo_app.contexts.tasks.domain.entities.task import OwnerId, Task
    from todo_app.contexts.tasks.domain.value_objects.task_id import TaskId
    from todo_app.contexts.tasks.domain.value_objects.task_status import TaskStatus
    from todo_app.contexts.users.domain.entities.user import User
    from todo_app.contexts.users.domain.value_objects.user_id import UserId


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published.append(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, User] = {}

    async def add(self, user: User) -> None:
        self._store[user.id.value] = user

    async def get(self, user_id: UserId) -> User | None:
        return self._store.get(user_id.value)

    async def get_by_email(self, email: Email) -> User | None:
        return next((u for u in self._store.values() if str(u.email) == str(email)), None)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        return list(self._store.values())[offset : offset + limit]

    async def count(self) -> int:
        return len(self._store)

    async def update(self, user: User) -> None:
        self._store[user.id.value] = user


class FakeTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Task] = {}

    async def add(self, task: Task) -> None:
        self._store[task.id.value] = task

    async def get(self, task_id: TaskId) -> Task | None:
        return self._store.get(task_id.value)

    async def list(
        self,
        *,
        owner_id: OwnerId | None = None,
        status: TaskStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        items = list(self._store.values())
        if owner_id is not None:
            items = [t for t in items if t.owner_id.value == owner_id.value]
        if status is not None:
            items = [t for t in items if t.status is status]
        return items[offset : offset + limit]

    async def count(
        self, *, owner_id: OwnerId | None = None, status: TaskStatus | None = None
    ) -> int:
        items = list(self._store.values())
        if owner_id is not None:
            items = [t for t in items if t.owner_id.value == owner_id.value]
        if status is not None:
            items = [t for t in items if t.status is status]
        return len(items)

    async def update(self, task: Task) -> None:
        self._store[task.id.value] = task

    async def delete(self, task_id: TaskId) -> None:
        self._store.pop(task_id.value, None)


class FakeSuggestionRepository(SuggestionRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, AiSuggestion] = {}

    async def add(self, suggestion: AiSuggestion) -> None:
        self._store[suggestion.id.value] = suggestion

    async def get(self, suggestion_id: SuggestionId) -> AiSuggestion | None:
        return self._store.get(suggestion_id.value)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[AiSuggestion]:
        return list(self._store.values())[offset : offset + limit]

    async def count(self) -> int:
        return len(self._store)

    async def update(self, suggestion: AiSuggestion) -> None:
        self._store[suggestion.id.value] = suggestion


class FakeLlmClient(LlmClient):
    def __init__(self, reply: str = "Do the most urgent task.", fail: bool = False) -> None:
        self._reply = reply
        self._fail = fail
        self.calls: list[str] = []

    async def complete(self, prompt: PromptText, model: ModelIdentifier) -> LlmCompletion:
        self.calls.append(str(prompt))
        if self._fail:
            raise RuntimeError("LLM unavailable")
        return LlmCompletion(text=self._reply, model=str(model))


class FakeUserLookup(UserLookupPort):
    def __init__(self, users: dict[UUID, UserSummary] | None = None) -> None:
        self._users = users or {}

    def add(self, summary: UserSummary) -> None:
        self._users[summary.id] = summary

    async def find(self, user_id: UUID) -> UserSummary | None:
        return self._users.get(user_id)


class FakeTaskRead(TaskReadPort):
    def __init__(self, briefs: list[TaskBrief] | None = None) -> None:
        self._briefs = briefs or []

    async def list_for_owner(self, owner_id: UUID, *, limit: int = 20) -> list[TaskBrief]:
        return self._briefs[:limit]
