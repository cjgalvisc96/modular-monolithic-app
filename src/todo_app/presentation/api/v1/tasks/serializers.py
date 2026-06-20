from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from todo_app.contexts.tasks.application.dto.task_dto import (
    CreateTaskInput,
    TaskOutput,
    UpdateTaskInput,
)


class CreateTaskRequest(BaseModel):
    owner_id: UUID
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    due_date: date | None = None

    def to_input(self) -> CreateTaskInput:
        return CreateTaskInput(
            owner_id=self.owner_id,
            title=self.title,
            description=self.description,
            due_date=self.due_date,
        )


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: date | None = None

    def to_input(self) -> UpdateTaskInput:
        return UpdateTaskInput(
            title=self.title, description=self.description, due_date=self.due_date
        )


class TaskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    owner_id: UUID
    title: str
    description: str
    status: str
    due_date: date | None

    @classmethod
    def from_output(cls, dto: TaskOutput) -> TaskResponse:
        return cls(
            id=dto.id,
            tenant_id=dto.tenant_id,
            owner_id=dto.owner_id,
            title=dto.title,
            description=dto.description,
            status=dto.status,
            due_date=dto.due_date,
        )
