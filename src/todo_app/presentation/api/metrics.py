"""Prometheus metrics — a scrape endpoint for the platform's collector."""

from __future__ import annotations

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency (seconds)", ["method"])

METRICS_PATH = "/metrics"


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == METRICS_PATH:
            return await call_next(request)
        started = time.perf_counter()
        response = await call_next(request)
        LATENCY.labels(request.method).observe(time.perf_counter() - started)
        REQUESTS.labels(request.method, str(response.status_code)).inc()
        return response


async def metrics_endpoint(request: Request) -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
