"""One-shot demo-data seeder, run as an init container before the API.

Drives the SAME application use cases the API calls (RegisterUserCommand /
CreateTaskCommand / CompleteTaskCommand) — it is an entrypoint, not business
logic. Idempotent: re-running a populated DB is a no-op.
"""

from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path
from uuid import UUID

from todo_app.contexts.shared.application.request_context import RequestContext, bind_context
from todo_app.contexts.shared.domain.exceptions import ConflictError
from todo_app.contexts.tasks.application.dto.task_dto import CreateTaskInput
from todo_app.contexts.users.application.dto.user_dto import RegisterUserInput
from todo_app.core.config import get_settings
from todo_app.core.di.container import ApplicationContainer, build_container

_DATA = Path("docker/mock-data")


def main() -> None:
    container = build_container(get_settings())
    users = json.loads((_DATA / "users.json").read_text())
    tasks = json.loads((_DATA / "tasks.json").read_text())
    tenants = {UUID(u["tenant_id"]) for u in users}
    try:
        asyncio.run(_seed_all(container, tenants, users, tasks))
    except ConflictError:
        print("Demo data already present; nothing to seed.")
        return
    print(f"Seeded {len(users)} users / {len(tasks)} tasks across {len(tenants)} tenant(s).")


async def _seed_all(
    container: ApplicationContainer, tenants: set[UUID], users: list[dict], tasks: list[dict]
) -> None:
    for tenant in tenants:
        with bind_context(RequestContext(tenant_id=tenant, roles=frozenset({"admin"}))):
            async with container.shared.unit_of_work().begin(tenant):
                await _seed_tenant(container, tenant, users, tasks)


async def _seed_tenant(
    container: ApplicationContainer, tenant: UUID, users: list[dict], tasks: list[dict]
) -> None:
    register = container.users.register_user_command()
    owner_ids: dict[str, UUID] = {}
    for u in (u for u in users if UUID(u["tenant_id"]) == tenant):
        created = await register.execute(
            tenant, RegisterUserInput(email=u["email"], full_name=u["full_name"], role=u["role"])
        )
        owner_ids[u["id"]] = created.id

    create_task = container.tasks.create_task_command()
    complete_task = container.tasks.complete_task_command()
    for t in (t for t in tasks if UUID(t["tenant_id"]) == tenant):
        due = t.get("due_date")
        created = await create_task.execute(
            tenant,
            CreateTaskInput(
                owner_id=owner_ids[t["owner_id"]],
                title=t["title"],
                description=t.get("description", ""),
                due_date=date.fromisoformat(due) if due else None,
            ),
        )
        if t.get("status") == "completed":
            await complete_task.execute(created.id)


if __name__ == "__main__":  # pragma: no cover
    main()
