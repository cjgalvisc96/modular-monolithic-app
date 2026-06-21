"""UsersContainer — wires the users context's use cases, repository, and Cognito."""

from dependency_injector import containers, providers

from todo_app.contexts.users.application.commands.change_user_role import (
    ChangeUserRoleCommand,
)
from todo_app.contexts.users.application.commands.register_user import RegisterUserCommand
from todo_app.contexts.users.application.queries.get_user import GetUserByIdQuery
from todo_app.contexts.users.application.queries.list_users import ListUsersQuery
from todo_app.contexts.users.domain.services.email_uniqueness import EmailUniquenessChecker
from todo_app.contexts.users.infrastructure.auth.cognito import CognitoAuthenticator
from todo_app.contexts.users.infrastructure.db.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


class UsersContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    shared = providers.DependenciesContainer()

    user_repository = providers.Factory(SqlAlchemyUserRepository)

    email_uniqueness = providers.Factory(EmailUniquenessChecker, repository=user_repository)

    register_user_command = providers.Factory(
        RegisterUserCommand,
        repository=user_repository,
        uniqueness=email_uniqueness,
        publisher=shared.event_publisher,
    )
    change_user_role_command = providers.Factory(ChangeUserRoleCommand, repository=user_repository)

    get_user_query = providers.Factory(GetUserByIdQuery, repository=user_repository)
    list_users_query = providers.Factory(ListUsersQuery, repository=user_repository)

    cognito_authenticator = providers.Singleton(
        CognitoAuthenticator,
        region=config.aws_region,
        user_pool_id=config.cognito_user_pool_id,
        app_client_id=config.cognito_app_client_id,
    )
