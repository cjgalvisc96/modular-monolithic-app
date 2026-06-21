"""ApplicationContainer — the single root composition point."""

from __future__ import annotations

from dependency_injector import containers, providers

from todo_app.contexts.ai.container import AiContainer
from todo_app.contexts.shared.container import SharedContainer
from todo_app.contexts.tasks.container import TasksContainer
from todo_app.contexts.users.container import UsersContainer
from todo_app.core.di.adapters import TasksTaskReadAdapter, UsersUserLookupAdapter


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    shared = providers.Container(SharedContainer, config=config)

    users = providers.Container(UsersContainer, config=config, shared=shared)

    user_lookup = providers.Factory(
        UsersUserLookupAdapter,
        user_repository_factory=users.user_repository.provider,
    )

    tasks = providers.Container(
        TasksContainer, config=config, shared=shared, user_lookup=user_lookup
    )

    task_read_port = providers.Factory(
        TasksTaskReadAdapter,
        task_repository_factory=tasks.task_repository.provider,
    )

    ai = providers.Container(
        AiContainer, config=config, shared=shared, task_read_port=task_read_port
    )


def build_container(settings=None) -> ApplicationContainer:
    from todo_app.core.config import get_settings

    settings = settings or get_settings()
    container = ApplicationContainer()
    container.config.from_dict(settings.as_provider_dict())
    return container
