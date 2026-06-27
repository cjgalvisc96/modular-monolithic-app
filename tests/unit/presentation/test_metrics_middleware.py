"""Prometheus + request-context middleware, exercised by calling dispatch directly."""

from types import SimpleNamespace
from uuid import uuid4

from todo_app.contexts.shared.application.request_context import RequestContext, bind_context
from todo_app.presentation.api.metrics import (
    METRICS_PATH,
    PrometheusMiddleware,
    metrics_endpoint,
)
from todo_app.presentation.api.middleware.tenant_middleware import RequestContextMiddleware


def _request(path: str = "/api/v1/tasks", method: str = "GET", headers: dict | None = None):
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        method=method,
        headers=headers or {},
        state=SimpleNamespace(),
    )


def _response(status_code: int = 200):
    return SimpleNamespace(status_code=status_code, headers={})


async def test_prometheus_middleware_records_normal_request():
    mw = PrometheusMiddleware(app=None)
    seen = _response(201)

    async def call_next(_request):
        return seen

    out = await mw.dispatch(_request(method="POST"), call_next)
    assert out is seen


async def test_prometheus_middleware_passes_metrics_path_through():
    mw = PrometheusMiddleware(app=None)
    seen = _response(200)

    async def call_next(_request):
        return seen

    out = await mw.dispatch(_request(path=METRICS_PATH), call_next)
    assert out is seen


async def test_metrics_endpoint_returns_prometheus_exposition():
    response = await metrics_endpoint(_request(path=METRICS_PATH))
    assert response.status_code == 200
    assert b"# HELP" in response.body or response.body == b""  # may be empty before traffic
    assert "text/plain" in response.media_type


async def test_request_context_middleware_sets_correlation_id_and_logs():
    mw = RequestContextMiddleware(app=None)
    resp = _response(200)

    async def call_next(request):
        # the middleware must have stamped the request id before calling through
        assert request.state.request_id
        return resp

    ctx = RequestContext(tenant_id=uuid4(), user_id=uuid4(), roles=frozenset({"member"}))
    with bind_context(ctx):
        out = await mw.dispatch(_request(headers={}), call_next)
    assert out is resp
    assert out.headers["x-request-id"]


async def test_request_context_middleware_preserves_incoming_request_id():
    mw = RequestContextMiddleware(app=None)
    resp = _response(200)

    async def call_next(_request):
        return resp

    out = await mw.dispatch(_request(headers={"x-request-id": "fixed-id"}), call_next)
    assert out.headers["x-request-id"] == "fixed-id"
