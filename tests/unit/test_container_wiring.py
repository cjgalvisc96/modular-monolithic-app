"""Asserts the root ApplicationContainer wires every provider, including the
cross-context bindings (tasks→users, ai→tasks)."""

from __future__ import annotations

from todo_app.contexts.ai.application.commands.generate_task_suggestion import (
    GenerateTaskSuggestionCommand,
)
from todo_app.contexts.tasks.application.commands.create_task import CreateTaskCommand
from todo_app.contexts.users.application.commands.register_user import RegisterUserCommand
from todo_app.core.di.adapters import TasksTaskReadAdapter, UsersUserLookupAdapter
from todo_app.core.di.container import build_container


def test_all_providers_resolve():
    c = build_container()

    assert isinstance(c.users.register_user_command(), RegisterUserCommand)
    assert isinstance(c.tasks.create_task_command(), CreateTaskCommand)
    assert isinstance(c.ai.generate_suggestion_command(), GenerateTaskSuggestionCommand)

    # cross-context adapters
    assert isinstance(c.user_lookup(), UsersUserLookupAdapter)
    assert isinstance(c.task_read_port(), TasksTaskReadAdapter)

    # shared infra
    assert c.shared.database() is c.shared.database()  # singleton
    assert c.shared.unit_of_work() is not None


def test_cross_context_adapters_are_injected_into_commands():
    c = build_container()
    # create_task_command must have received the user_lookup adapter
    create = c.tasks.create_task_command()
    assert create._user_lookup is not None
    generate = c.ai.generate_suggestion_command()
    assert generate._tasks is not None
