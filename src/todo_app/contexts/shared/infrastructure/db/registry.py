"""Single import point that registers every ORM model on the shared metadata."""

from todo_app.contexts.ai.infrastructure.db.models import AiSuggestionModel
from todo_app.contexts.shared.infrastructure.db.base_model import Base
from todo_app.contexts.tasks.infrastructure.db.models import TaskModel
from todo_app.contexts.users.infrastructure.db.models import UserModel

__all__ = ["AiSuggestionModel", "Base", "TaskModel", "UserModel", "metadata"]

metadata = Base.metadata
