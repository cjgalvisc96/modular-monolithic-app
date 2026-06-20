"""AiContainer — wires the ai context. Receives a read-only task lookup port
(``task_read_port``) from the root (ai → tasks). The LLM client is the Bedrock
adapter, or a deterministic stub when DEBUG and no AWS creds are configured."""

from __future__ import annotations

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
    """Use the real Bedrock adapter in non-debug; stub locally so the AI flow
    works without AWS credentials."""
    if debug:
        return StubLlmClient()
    return BedrockLlmClient(region=region)


class AiContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    shared = providers.DependenciesContainer()

    # Cross-context dependency satisfied at the root (tasks → ai read side).
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
