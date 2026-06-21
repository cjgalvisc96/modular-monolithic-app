"""Entity ↔ ORM model mapping. The only place that knows both shapes."""

from __future__ import annotations

from todo_app.contexts.shared.domain.value_objects.email import Email
from todo_app.contexts.shared.domain.value_objects.tenant_id import TenantId
from todo_app.contexts.users.domain.entities.user import User
from todo_app.contexts.users.domain.value_objects.role import Role
from todo_app.contexts.users.domain.value_objects.user_id import UserId
from todo_app.contexts.users.infrastructure.db.models.user_model import UserModel


class UserMapper:
    @staticmethod
    def to_entity(model: UserModel) -> User:
        return User(
            id=UserId(model.id),
            tenant_id=TenantId(model.tenant_id),
            email=Email(model.email),
            full_name=model.full_name,
            role=Role.parse(model.role),
            is_active=model.is_active,
        )

    @staticmethod
    def to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            email=str(entity.email),
            full_name=entity.full_name,
            role=entity.role.value,
            is_active=entity.is_active,
        )

    @staticmethod
    def apply(entity: User, model: UserModel) -> None:
        model.email = str(entity.email)
        model.full_name = entity.full_name
        model.role = entity.role.value
        model.is_active = entity.is_active
