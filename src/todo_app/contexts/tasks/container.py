"""TasksContainer — wires the tasks context. Receives a read-only user lookup
port (``user_lookup``) injected by the root ApplicationContainer; tasks never
imports users internals."""

from __future__ import annotations

from dependency_injector import containers, providers

from todo_app.contexts.tasks.application.commands.complete_task import CompleteTaskCommand
from todo_app.contexts.tasks.application.commands.create_task import CreateTaskCommand
from todo_app.contexts.tasks.application.commands.update_task import UpdateTaskCommand
from todo_app.contexts.tasks.application.queries.get_task import GetTaskQuery
from todo_app.contexts.tasks.application.queries.list_tasks import ListTasksQuery
from todo_app.contexts.tasks.infrastructure.db.repositories.sqlalchemy_task_repository import (
    SqlAlchemyTaskRepository,
)


class TasksContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    shared = providers.DependenciesContainer()

    # Cross-context dependency satisfied at the root (users → tasks).
    user_lookup = providers.Dependency()

    task_repository = providers.Factory(SqlAlchemyTaskRepository)

    # --- commands ---
    create_task_command = providers.Factory(
        CreateTaskCommand,
        repository=task_repository,
        user_lookup=user_lookup,
        publisher=shared.event_publisher,
    )
    complete_task_command = providers.Factory(
        CompleteTaskCommand,
        repository=task_repository,
        publisher=shared.event_publisher,
    )
    update_task_command = providers.Factory(UpdateTaskCommand, repository=task_repository)

    # --- queries ---
    get_task_query = providers.Factory(GetTaskQuery, repository=task_repository)
    list_tasks_query = providers.Factory(ListTasksQuery, repository=task_repository)
