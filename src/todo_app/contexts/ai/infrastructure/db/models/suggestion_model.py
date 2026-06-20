from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from todo_app.contexts.shared.infrastructure.db.base_model import BaseModel


class AiSuggestionModel(BaseModel):
    """Persisted AI suggestion history — tenant-isolated, RLS-covered like the rest."""

    __tablename__ = "ai_suggestions"

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
