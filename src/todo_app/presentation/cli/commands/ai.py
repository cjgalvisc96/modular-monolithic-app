from uuid import UUID

import typer

from todo_app.contexts.ai.application.dto.suggestion_dto import GenerateSuggestionInput
from todo_app.presentation.cli.runtime import container, run_in_context

app = typer.Typer(help="AI suggestion commands.")


@app.command("generate-suggestion")
def generate_suggestion(
    tenant: UUID = typer.Option(..., help="Tenant id"),
    owner: UUID = typer.Option(..., help="Owner user id"),
    instruction: str = typer.Option(
        "Suggest the next task I should focus on.", help="Instruction for the model"
    ),
) -> None:
    command = container().ai.generate_suggestion_command()
    result = run_in_context(
        tenant,
        lambda: command.execute(
            tenant, GenerateSuggestionInput(owner_id=owner, instruction=instruction)
        ),
    )
    typer.echo(f"[{result.status}] {result.response}")
