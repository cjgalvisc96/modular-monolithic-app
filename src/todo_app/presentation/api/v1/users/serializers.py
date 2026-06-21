"""HTTP serializers for the users context; map to/from application DTOs, never DB models."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from todo_app.contexts.users.application.dto.user_dto import RegisterUserInput, UserOutput


class RegisterUserRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    role: str = "member"

    def to_input(self) -> RegisterUserInput:
        return RegisterUserInput(email=str(self.email), full_name=self.full_name, role=self.role)


class ChangeRoleRequest(BaseModel):
    role: str


class UserResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    @classmethod
    def from_output(cls, dto: UserOutput) -> UserResponse:
        return cls(
            id=dto.id,
            tenant_id=dto.tenant_id,
            email=dto.email,
            full_name=dto.full_name,
            role=dto.role,
            is_active=dto.is_active,
        )
