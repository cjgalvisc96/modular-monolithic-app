"""ASGI entrypoint for the HTTP API.

``app`` is the ASGI application — used by uvicorn and the container image:
``uvicorn todo_app.presentation.api.main:app``. ``main()`` is the console-script
runner wired to the ``todo-api`` entry point in pyproject.toml.
"""

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


def main() -> None:
    """Console-script entry point (``todo-api``): serve the API with uvicorn.

    Hot-reload is enabled when ``API_RELOAD`` is truthy (set in the dev image),
    off otherwise (prod). Host/port default to all-interfaces:8000 by design.
    """
    import os

    import uvicorn

    reload = os.environ.get("API_RELOAD", "").lower() in {"1", "true", "yes", "on"}
    uvicorn.run(
        "todo_app.presentation.api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("API_PORT", "8000")),
        reload=reload,
        reload_dirs=["src"] if reload else None,
    )
