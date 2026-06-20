# Role: SRE

## Mission

Own reliability and observability: the OpenTelemetry instrumentation, the Grafana/Tempo/Prometheus
stack, and the operational posture that keeps the service healthy and debuggable in production.

## Responsibilities

- Maintain OpenTelemetry instrumentation in `core/telemetry.py` — FastAPI, SQLAlchemy, Redis, and
  outbound AWS calls (Cognito, Bedrock) — so any request is one end-to-end trace.
- Maintain the OTel Collector config (`observability/otel-collector-config.yaml`) and Grafana
  dashboards (`observability/grafana/dashboards/`): request latency, error rate, DB pool
  saturation, cache hit rate.
- Define SLOs and alerting on the golden signals; own on-call runbooks and incident response.
- Watch reliability risks: DB connection pool saturation, RLS-driven fail-closed behavior (a missing
  `app.tenant_id` yields zero rows), cache health, and Bedrock latency/error budgets.

## Inputs

- Telemetry from the running system; reliability requirements from the Lead.
- The [Observability](../../docs/operations/observability.md) page and the DevOps role's
  infrastructure.

## Outputs

- Working end-to-end traces, dashboards, alerts, and runbooks.
- Incident reviews and reliability findings fed back to the Lead, Developer, and DevOps.

## Boundaries — the SRE role must NOT

- Disable or weaken tenant isolation (RLS) or auth to "fix" an availability issue — fail closed is
  correct; a tenant seeing another tenant's data is never an acceptable mitigation.
- Add instrumentation that violates layer purity (e.g. telemetry leaking infrastructure concerns
  into the domain).
- Broaden IAM/IRSA scopes or alter application contracts to ease operations.
- Take over feature implementation or test authoring.

## Conventions enforced

- A single request (API → use case → repository → DB, plus any Redis/Bedrock spans) is traceable as
  one trace in Grafana/Tempo.
- Observability respects the architecture: instrumentation is wired in `core/telemetry.py`, not
  scattered into domain/application code.
- Reliability practices honor the tenancy and IAM model — RLS as the data boundary, least-privilege
  IRSA per workload.
