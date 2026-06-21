"""Wires the ai context; receives a read-only task lookup port from the root (ai → tasks)."""

from dependency_injector import containers, providers

from todo_app.contexts.ai.application.commands.generate_task_suggestion import (
    GenerateTaskSuggestionCommand,
)
from todo_app.contexts.ai.application.queries.list_suggestions import ListSuggestionsQuery
from todo_app.contexts.ai.infrastructure.bedrock.bedrock_client import BedrockLlmClient
from todo_app.contexts.ai.infrastructure.bedrock.stub_client import StubLlmClient
from todo_app.contexts.ai.infrastructure.db.repositories.sqlalchemy_suggestion_repository import (
    SqlAlchemySuggestionRepository,
)


def _build_llm_client(debug: bool, region: str):
    if debug:
        return StubLlmClient()
    return BedrockLlmClient(region=region)


class AiContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    shared = providers.DependenciesContainer()

    task_read_port = providers.Dependency()

    suggestion_repository = providers.Factory(SqlAlchemySuggestionRepository)

    llm_client = providers.Singleton(
        _build_llm_client, debug=config.debug, region=config.aws_region
    )

    generate_suggestion_command = providers.Factory(
        GenerateTaskSuggestionCommand,
        repository=suggestion_repository,
        llm_client=llm_client,
        task_read_port=task_read_port,
        model_id=config.bedrock_model_id,
    )

    list_suggestions_query = providers.Factory(
        ListSuggestionsQuery, repository=suggestion_repository
    )
