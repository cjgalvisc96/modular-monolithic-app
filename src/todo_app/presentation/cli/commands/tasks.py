from __future__ import annotations

from uuid import UUID

import typer

from todo_app.contexts.tasks.application.dto.task_dto import CreateTaskInput
from todo_app.presentation.cli.runtime import container, run_in_context

app = typer.Typer(help="Task operational commands.")


@app.command("create")
def create_task(
    tenant: UUID = typer.Option(..., help="Tenant id"),
    owner: UUID = typer.Option(..., help="Owner user id"),
    title: str = typer.Option(..., help="Task title"),
    description: str = typer.Option("", help="Task description"),
) -> None:
    command = container().tasks.create_task_command()
    result = run_in_context(
        tenant,
        lambda: command.execute(
            tenant, CreateTaskInput(owner_id=owner, title=title, description=description)
        ),
    )
    typer.echo(f"Created task {result.id} '{result.title}' [{result.status}]")


@app.command("list")
def list_tasks(tenant: UUID = typer.Option(..., help="Tenant id")) -> None:
    query = container().tasks.list_tasks_query()
    results = run_in_context(tenant, lambda: query.execute())
    for t in results:
        typer.echo(f"{t.id}  [{t.status:11}]  {t.title}")


@app.command("complete")
def complete_task(
    tenant: UUID = typer.Option(..., help="Tenant id"),
    task_id: UUID = typer.Argument(..., help="Task id"),
) -> None:
    command = container().tasks.complete_task_command()
    result = run_in_context(tenant, lambda: command.execute(task_id))
    typer.echo(f"Completed task {result.id} [{result.status}]")
