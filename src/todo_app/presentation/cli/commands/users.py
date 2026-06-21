from uuid import UUID

import typer

from todo_app.contexts.users.application.dto.user_dto import RegisterUserInput
from todo_app.presentation.cli.runtime import container, run_in_context

app = typer.Typer(help="User administration commands.")


@app.command("create-admin")
def create_admin(
    tenant: UUID = typer.Option(..., help="Tenant id"),
    email: str = typer.Option(..., help="Admin email"),
    full_name: str = typer.Option(..., help="Full name"),
) -> None:
    """Register an admin user (same RegisterUserCommand the API uses)."""
    command = container().users.register_user_command()
    result = run_in_context(
        tenant,
        lambda: command.execute(
            tenant, RegisterUserInput(email=email, full_name=full_name, role="admin")
        ),
    )
    typer.echo(f"Created admin {result.email} ({result.id})")


@app.command("list")
def list_users(tenant: UUID = typer.Option(..., help="Tenant id")) -> None:
    query = container().users.list_users_query()
    results = run_in_context(tenant, lambda: query.execute())
    for u in results:
        typer.echo(f"{u.id}  {u.email:30}  {u.role}")
