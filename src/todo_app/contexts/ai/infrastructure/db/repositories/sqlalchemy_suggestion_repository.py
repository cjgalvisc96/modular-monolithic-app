from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from todo_app.contexts.ai.domain.repositories.suggestion_repository import (
    SuggestionRepository,
)
from todo_app.contexts.ai.infrastructure.db.models.suggestion_model import AiSuggestionModel
from todo_app.contexts.ai.infrastructure.mappers.suggestion_mapper import SuggestionMapper
from todo_app.contexts.shared.infrastructure.db.scoped_session import current_session

if TYPE_CHECKING:
    from todo_app.contexts.ai.domain.entities.ai_suggestion import AiSuggestion
    from todo_app.contexts.ai.domain.value_objects.suggestion_id import SuggestionId


class SqlAlchemySuggestionRepository(SuggestionRepository):
    async def add(self, suggestion: AiSuggestion) -> None:
        session = current_session()
        session.add(SuggestionMapper.to_model(suggestion))
        await session.flush()

    async def get(self, suggestion_id: SuggestionId) -> AiSuggestion | None:
        session = current_session()
        model = await session.get(AiSuggestionModel, suggestion_id.value)
        if model is None or model.is_deleted:
            return None
        return SuggestionMapper.to_entity(model)

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[AiSuggestion]:
        session = current_session()
        stmt = (
            select(AiSuggestionModel)
            .where(AiSuggestionModel.deleted_at.is_(None))
            .order_by(AiSuggestionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = (await session.execute(stmt)).scalars().all()
        return [SuggestionMapper.to_entity(m) for m in models]

    async def count(self) -> int:
        session = current_session()
        stmt = (
            select(func.count())
            .select_from(AiSuggestionModel)
            .where(AiSuggestionModel.deleted_at.is_(None))
        )
        return int((await session.execute(stmt)).scalar_one())

    async def update(self, suggestion: AiSuggestion) -> None:
        session = current_session()
        model = await session.get(AiSuggestionModel, suggestion.id.value)
        if model is None:
            raise ValueError(f"Suggestion not found for update: {suggestion.id}")
        SuggestionMapper.apply(suggestion, model)
        await session.flush()
