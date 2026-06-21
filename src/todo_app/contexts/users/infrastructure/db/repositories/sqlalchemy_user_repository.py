"""Tenant scoping is enforced by RLS; the WHERE on tenant_id is defense-in-depth only."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from todo_app.contexts.shared.infrastructure.db.scoped_session import current_session
from todo_app.contexts.users.domain.repositories.user_repository import UserRepository
from todo_app.contexts.users.infrastructure.db.models.user_model import UserModel
from todo_app.contexts.users.infrastructure.mappers.user_mapper import UserMapper

if TYPE_CHECKING:
    from todo_app.contexts.shared.domain.value_objects.email import Email
    from todo_app.contexts.users.domain.entities.user import User
    from todo_app.contexts.users.domain.value_objects.user_id import UserId


class SqlAlchemyUserRepository(UserRepository):
    async def add(self, user: User) -> None:
        session = current_session()
        session.add(UserMapper.to_model(user))
        await session.flush()

    async def get(self, user_id: UserId) -> User | None:
        session = current_session()
        model = await session.get(UserModel, user_id.value)
        if model is None or model.is_deleted:
            return None
        return UserMapper.to_entity(model)

    async def get_by_email(self, email: Email) -> User | None:
        session = current_session()
        stmt = select(UserModel).where(
            UserModel.email == str(email), UserModel.deleted_at.is_(None)
        )
        model = (await session.execute(stmt)).scalar_one_or_none()
        return UserMapper.to_entity(model) if model else None

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[User]:
        session = current_session()
        stmt = (
            select(UserModel)
            .where(UserModel.deleted_at.is_(None))
            .order_by(UserModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        models = (await session.execute(stmt)).scalars().all()
        return [UserMapper.to_entity(m) for m in models]

    async def count(self) -> int:
        session = current_session()
        stmt = select(func.count()).select_from(UserModel).where(UserModel.deleted_at.is_(None))
        return int((await session.execute(stmt)).scalar_one())

    async def update(self, user: User) -> None:
        session = current_session()
        model = await session.get(UserModel, user.id.value)
        if model is None:
            raise ValueError(f"User not found for update: {user.id}")
        UserMapper.apply(user, model)
        await session.flush()
