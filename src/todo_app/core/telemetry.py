# OTel packages live in the optional `observability` dependency group, so they
# may be absent in a base install — guarded by try/except at runtime.
# pyright: reportMissingImports=false
"""OpenTelemetry wiring (no-op unless OTEL_ENABLE is set).

Instruments FastAPI, SQLAlchemy, Redis, and outbound AWS (botocore) calls so a
request is traceable API → use case → repository → DB. Imports are lazy so the
OTel SDK is an optional dependency group (`--group observability`).
"""

from __future__ import annotations

import logging

logger = logging.getLogger("todo_app.telemetry")


def setup_telemetry(app, container, settings) -> None:
    if not getattr(settings, "otel_enable", False):
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning("OTEL_ENABLE set but opentelemetry not installed; skipping")
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
    )
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    try:
        engine = container.shared.database().engine.sync_engine
        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception:
        logger.debug("SQLAlchemy instrumentation skipped")
    RedisInstrumentor().instrument()
    BotocoreInstrumentor().instrument()
    logger.info("OpenTelemetry enabled (service=%s)", settings.otel_service_name)
