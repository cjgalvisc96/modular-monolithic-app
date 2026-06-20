# Observability stack (Phase 11)

Deployment-side configuration for the `todo-app` telemetry pipeline. The
application code is already instrumented — see
[`src/todo_app/core/telemetry.py`](../src/todo_app/core/telemetry.py). This
directory provides the collector, backends and dashboards that turn that
instrumentation into something you can look at.

## How the pieces fit together

```
                         OTLP/gRPC :4317
  ┌──────────────┐  (spans + metrics)   ┌──────────────────────┐
  │  todo-app    │ ───────────────────▶ │  OTel Collector       │
  │ (OTel SDK)   │                      │  todo-app-otel-       │
  └──────────────┘                      │  collector            │
                                        └───────┬───────┬───────┘
                                  traces (OTLP) │       │ metrics
                                                ▼       ▼ (Prom :8889)
                                       ┌─────────┐   ┌────────────┐
                                       │  Tempo  │   │ Prometheus │
                                       │ todo-   │   │ todo-app-  │
                                       │ app-    │   │ prometheus │
                                       │ tempo   │   └─────┬──────┘
                                       └────┬────┘         │
                                            │              │
                                            ▼              ▼
                                       ┌──────────────────────┐
                                       │       Grafana         │
                                       │   todo-app-grafana    │
                                       │ (datasources + 5      │
                                       │  provisioned          │
                                       │  dashboards)          │
                                       └──────────────────────┘
```

- **App (OTel SDK):** `setup_telemetry()` instruments FastAPI, SQLAlchemy,
  Redis and botocore, and exports spans via the OTLP/gRPC span exporter to
  `OTEL_EXPORTER_OTLP_ENDPOINT`. Wiring is a no-op unless `OTEL_ENABLE=true`.
- **OTel Collector** (`otel-collector-config.yaml`): receives OTLP on
  `:4317` (gRPC) and `:4318` (HTTP), batches/limits/enriches, then fans out —
  traces to Tempo over OTLP, metrics to a Prometheus pull endpoint on `:8889`.
- **Tempo** (`tempo/tempo.yaml`): trace store (local filesystem backend),
  queried by Grafana.
- **Prometheus** (`prometheus/prometheus.yml`): scrapes the collector's
  `:8889` exporter (app metrics) and `:8888` (collector internals).
- **Grafana**: provisioned with both datasources and five dashboards.

## Enabling telemetry in the app

Telemetry is gated on `OTEL_ENABLE`. Set these in the app environment (`.env`
or container env):

```bash
OTEL_ENABLE=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://todo-app-otel-collector:4317
OTEL_SERVICE_NAME=todo-app
```

The OTel SDK and instrumentation packages live in the optional
`observability` dependency group:

```bash
uv sync --group observability
```

`telemetry.py` imports them lazily; if the group is not installed it logs a
warning and runs as a no-op, so a base install is unaffected.

## Running the local stack

The observability compose file joins the **existing** `todo-app-net` network
(declared `external: true`) so the app container can reach the collector by
name. Bring up the app stack first, then layer the observability stack:

```bash
# from the repo root
docker compose -f docker-compose.yml \
  -f observability/docker-compose.observability.yml up -d
```

Container names follow the project convention (`todo-app-<role>`):
`todo-app-otel-collector`, `todo-app-tempo`, `todo-app-prometheus`,
`todo-app-grafana`.

| UI / endpoint        | URL                              |
| -------------------- | -------------------------------- |
| Grafana              | http://localhost:3000 (admin/admin) |
| Prometheus           | http://localhost:9090            |
| Tempo query API      | http://localhost:3200            |
| Collector OTLP gRPC  | localhost:4317                   |
| Collector OTLP HTTP  | localhost:4318                   |
| Collector Prom expo. | http://localhost:8889/metrics    |

Grafana auto-loads the Prometheus and Tempo datasources and the dashboards in
`grafana/dashboards/` (folder `todo-app`).

## Dashboards

| File                         | Shows                                         |
| ---------------------------- | --------------------------------------------- |
| `request-latency.json`       | p50/p95/p99 HTTP server duration by route     |
| `error-rate.json`            | 5xx ratio and request rate by status class    |
| `db-pool-saturation.json`    | SQLAlchemy connection pool used/idle/pending  |
| `cache-hit-rate.json`        | Redis cache hit ratio and command latency     |
| `service-overview.json`      | combined RED + DB + cache signals             |

PromQL targets the OpenTelemetry metric names as re-exported by the
collector's Prometheus exporter (e.g. `http_server_duration_milliseconds_*`,
`db_client_connections_*`, `cache_hits_total` / `cache_misses_total`). Some
panels depend on metrics that only appear once the corresponding views/meters
are emitting; they render empty until data flows, which is expected.

## Exit criterion: a single end-to-end trace

The design's exit criterion is that **one request traced API → use case →
repository → DB shows as a single trace** in Grafana/Tempo. This works because
all instrumentation in `telemetry.py` shares one `TracerProvider`, and OTel
propagates the active trace context across the call stack within a request:

1. `FastAPIInstrumentor` opens the **root server span** when the request hits
   the API and makes its trace/span id the active context for that request.
2. The use case runs inside that context. Any DB access goes through the
   `SQLAlchemyInstrumentor`-wrapped engine, which opens **child spans** for
   each statement, parented to the active span.
3. `RedisInstrumentor` and `BotocoreInstrumentor` likewise create child spans
   for cache reads/writes and outbound AWS (Cognito/Bedrock) calls under the
   same trace.
4. All spans share one `trace_id`, are batched by `BatchSpanProcessor`,
   exported over OTLP to the collector, forwarded to Tempo, and reassembled
   into a single trace.

To verify end to end:

1. Start the app with `OTEL_ENABLE=true` and the stack above.
2. Hit an endpoint that touches the DB, e.g. `GET /api/v1/todos`.
3. In Grafana → **Explore** → **Tempo**, run a TraceQL search such as
   `{ resource.service.name = "todo-app" }` (or search by route).
4. Open the trace — you should see the FastAPI server span as the root with
   nested SQLAlchemy (and any Redis/botocore) spans beneath it, all under one
   trace id.
