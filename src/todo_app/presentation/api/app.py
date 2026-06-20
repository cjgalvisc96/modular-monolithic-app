"""FastAPI application assembled via a Builder.

Each private step configures one concern; ``create_api()`` returns the final
app. The builder owns the Settings + DI container and exposes a health check
that pings the real DB and Redis.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from todo_app.core.config import Settings, get_settings
from todo_app.core.di.container import ApplicationContainer, build_container
from todo_app.presentation.api.errors import register_exception_handlers
from todo_app.presentation.api.middleware.tenant_middleware import RequestContextMiddleware
from todo_app.presentation.api.v1.ai.routers import router as ai_router
from todo_app.presentation.api.v1.tasks.routers import router as tasks_router
from todo_app.presentation.api.v1.users.routers import router as users_router

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class ApiBuilder:
    def __init__(
        self, settings: Settings | None = None, container: ApplicationContainer | None = None
    ) -> None:
        self._settings = settings or get_settings()
        self._container = container or build_container(self._settings)
        self._app: FastAPI | None = None

    # --- builder steps -------------------------------------------------------
    def mount_di_container(self, container: ApplicationContainer | None = None) -> ApiBuilder:
        if container is not None:
            self._container = container
        return self

    async def check_dependencies(self) -> dict[str, str]:
        """Backs /health — pings DB and Redis."""
        statuses: dict[str, str] = {}
        try:
            await self._container.shared.database().ping()
            statuses["database"] = "ok"
        except Exception as exc:
            statuses["database"] = f"error: {exc}"
        try:
            await self._container.shared.cache().ping()
            statuses["redis"] = "ok"
        except Exception as exc:
            statuses["redis"] = f"error: {exc}"
        return statuses

    def _configure_middleware(self, app: FastAPI) -> None:
        app.add_middleware(RequestContextMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self._settings.cors_origin_list,
            allow_credentials=self._settings.cors_allow_credentials,
            allow_methods=[m.strip() for m in self._settings.cors_allow_methods.split(",")],
            allow_headers=[h.strip() for h in self._settings.cors_allow_headers.split(",")],
        )

    def _register_routes(self, app: FastAPI) -> None:
        @app.get("/health", tags=["meta"])
        async def health() -> JSONResponse:
            statuses = await self.check_dependencies()
            healthy = all(v == "ok" for v in statuses.values())
            return JSONResponse(
                status_code=200 if healthy else 503,
                content={"status": "ok" if healthy else "degraded", "checks": statuses},
            )

        @app.get("/", tags=["meta"])
        async def root() -> dict[str, str]:
            return {"service": self._settings.otel_service_name, "docs": "/docs"}

    def _register_routers(self, app: FastAPI) -> None:
        for router in (users_router, tasks_router, ai_router):
            app.include_router(router, prefix="/api/v1")

    def _mount_documentation(self, app: FastAPI) -> None:
        # FastAPI serves /docs and /redoc by default; kept explicit for clarity.
        app.docs_url = "/docs"
        app.redoc_url = "/redoc"

    def _mount_metrics(self, app: FastAPI) -> None:
        """Expose Prometheus metrics at /metrics for scrape-based platforms.

        The local-gitops OTel Collector scrapes pods by ``prometheus.io/*``
        annotation (no OTLP receiver), so the app publishes a scrape endpoint.
        """
        from todo_app.presentation.api.metrics import (
            METRICS_PATH,
            PrometheusMiddleware,
            metrics_endpoint,
        )

        app.add_middleware(PrometheusMiddleware)
        app.add_route(METRICS_PATH, metrics_endpoint, include_in_schema=False)

    def _create_lifespan(self):
        container = self._container
        settings = self._settings

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            app.state.container = container
            app.state.settings = settings
            # Warm the DB pool (best-effort; health surfaces real status).
            with suppress(Exception):
                await container.shared.database().ping()
            yield
            await container.shared.database().dispose()
            with suppress(Exception):
                await container.shared.cache().close()

        return lifespan

    # --- assembly ------------------------------------------------------------
    def create_api(self) -> FastAPI:
        app = FastAPI(
            title="TODO App",
            version="0.1.0",
            debug=self._settings.debug,
            lifespan=self._create_lifespan(),
        )
        # Ensure state is set even before lifespan (e.g. under TestClient calls).
        app.state.container = self._container
        app.state.settings = self._settings
        self._configure_middleware(app)
        self._register_routes(app)
        self._register_routers(app)
        self._mount_documentation(app)
        self._mount_metrics(app)
        register_exception_handlers(app)
        self._app = app
        return app


def create_app(
    settings: Settings | None = None, container: ApplicationContainer | None = None
) -> FastAPI:
    return ApiBuilder(settings, container).create_api()
