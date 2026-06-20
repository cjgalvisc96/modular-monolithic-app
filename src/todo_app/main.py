"""Application bootstrap — the ASGI entrypoint (``uvicorn todo_app.main:app``)."""

from __future__ import annotations

from todo_app.core.config import get_settings
from todo_app.core.di.container import build_container
from todo_app.core.logging import configure_logging
from todo_app.core.telemetry import setup_telemetry
from todo_app.presentation.api.app import create_app

settings = get_settings()
configure_logging(settings.log_level)
container = build_container(settings)

app = create_app(settings=settings, container=container)
setup_telemetry(app, container, settings)
