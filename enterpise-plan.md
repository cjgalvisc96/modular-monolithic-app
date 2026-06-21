# Enterprise Readiness Plan — Application Repo Scope

> **Scope:** only changes inside `cjgalvisc96/modular-monolithic-app`. Platform install
> (cert-manager, Keycloak server, CNI, Kyverno, Loki, Alertmanager, DB/cache backends)
> lives in `cjgalvisc96/local-gitops` and is assumed as a prerequisite.
> Target is fully local (kind + floci); **Keycloak** is the SSO provider.
>
> **Synced to commit `aff1cd1` (2026-06-21).** This revision marks items the repo has
> since implemented and narrows the remaining work.

---

## ✅ Landed since the last revision (verify-and-close)

The repo moved on several Priority-1 items. These are now **done or partially done**:

- **Rate limiting** — `presentation/api/middleware/rate_limit.py` adds a Redis-backed,
  fixed-window limiter, wired in `ApiBuilder._configure_middleware`, config-driven
  (`rate_limit_enabled/requests/window_seconds`), with unit tests. *Fails open* if Redis
  is down, and exempts `/health`, `/metrics`, `/docs`, etc.
  → **Remaining:** it keys on **client IP only**. Add a **per-tenant** dimension and a
  **stricter bucket for `/api/v1/ai/*`** (see Priority 6). Note the fail-open choice is a
  deliberate availability tradeoff — fine for now, document it.
- **CORS is now config-driven** — `cors_origin_list` + method/header parsing replace the
  old hardcoded `*`. → **Remaining:** still **defaults to `*` with credentials true** and
  has **no fail-fast**; that combination is invalid in prod (Priority 1.5 stays).
- **Caching layer** — `shared/infrastructure/cache/redis_cache.py` + `cache_*` settings.
  Good for the connection-pool/latency story; no enterprise action needed beyond cache-key
  tenant-scoping hygiene.
- **ECR publish workflow** — `.github/workflows/ecr.yml` (OIDC build→push→pull, self-skips
  without `AWS_ROLE_ARN`). This is the hook for Priority 4 signing/SBOM to plug into.
- **Error handler refactor** — `errors.py` was rewritten to a status-map + handler, but it
  **still returns `str(exc)`** in the body and still funnels unknowns to 400 (Priority 1.6
  stays).

---

## What you'll touch in this repo

| Path | What changes here |
|------|-------------------|
| `…/users/infrastructure/auth/` | `cognito.py` → generic OIDC (Keycloak) authenticator |
| `…/api/middleware/` | security headers; extend `rate_limit.py` (per-tenant + AI bucket) |
| `…/api/app.py`, `errors.py` | header middleware wiring; error hygiene |
| `core/config.py` | OIDC keys; CORS fail-fast validator |
| `contexts/ai/` | Bedrock adapter → config-driven model + quotas/circuit breaker |
| `infra/k8s/helm/` | ingress TLS, PDB, NetworkPolicy, startupProbe, preStop, annotations |
| `infra/terraform/` | cert/WAF variable validation, TLS min-version (AWS path) |
| `migrations/` | expand-contract discipline |
| `.github/workflows/` | scanning, SBOM, image signing (extend `ecr.yml`), pin actions |
| `Dockerfile` | pin base image by digest |
| `docs/` | ADR-0007 + operational runbooks |

## Prerequisites owned by `local-gitops` (out of scope)

cert-manager + CA `ClusterIssuer`; the **Keycloak server** + realm; a CNI that enforces
NetworkPolicy (Calico/Cilium — kindnet does not); ingress-nginx with ModSecurity/CRS;
Kyverno (admission); Loki + Alertmanager; Postgres/Redis (or CNPG/PgBouncer). The app's
chart only *references* these.

---

## Priority 0 — Identity: OIDC/Keycloak authenticator (app code)

**Status: not started — `cognito.py` is still the only authenticator.**

- Generalize `CognitoAuthenticator` → `OidcAuthenticator` (same RS256/JWKS verification;
  already provider-agnostic). Make issuer, JWKS URL, audience pure config.
- Read `tenant_id` and `realm_access.roles` instead of `custom:tenant_id` /
  `cognito:groups`.
- Rebind in the **`users` DI container**. `RequestContext`, RLS, `require_role` unchanged.
- Add `oidc_issuer` / `oidc_jwks_url` / `oidc_audience` to `core/config.py`, surfaced via
  the Helm ConfigMap + floci SSM like the Cognito keys.
- **Keep** the DEBUG-only `X-Dev-Tenant` / `X-Dev-Roles` bypass for tests.
- Commit the **realm-export JSON** (client + groups + `tenant_id` protocol mapper) as a
  fixture under `docs/` or `tests/support/`.
- Add **ADR-0007** recording the local Cognito→Keycloak reversal of ADR-0002.

---

## Priority 1 — Edge security & HTTPS

### App code
- **Security headers middleware** — *not present anywhere yet.* Add HSTS,
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, CSP
  (mind `/docs` + `/redoc`); register it in `ApiBuilder._configure_middleware`.
- **CORS fail-fast** — refuse to start in non-debug when `cors_allow_origins="*"` and
  `cors_allow_credentials=true`; require an explicit allowlist. (Config is now parsed, so
  this is a small validator on `Settings`.)
- **Error hygiene** (`errors.py`) — stop returning `str(exc)` on 5xx/unknown; return a
  generic body + the existing `x-request-id`; log detail server-side. The current rewrite
  kept the leak, so this is still open.
- **Rate limiting** — *exists.* Extend with per-tenant keying and the AI bucket.

### App Helm chart (`infra/k8s/helm/`) — none of these templates exist yet
- Add a gated `tls:` block to `ingress.yaml` + cert-manager annotation.
- Set `ssl-redirect`/`force-ssl-redirect` true in `values-prod.yaml`.
- Add ingress annotations to enable ModSecurity/CRS and `limit-rps`/`limit-connections`
  (defence-in-depth alongside the app-level limiter).

### Terraform (AWS path)
- Require `acm_certificate_arn` in prod (validation); pin `TLSv1.2_2021`; require a
  `web_acl_id` in prod.

---

## Priority 2 — Runtime resilience (app Helm chart + lifespan)

**Status: not started — chart has no PDB/NetworkPolicy/startupProbe/preStop.**

- **PodDisruptionBudget** template (`minAvailable: 2`).
- **startupProbe** on `/health`, decoupled from liveness.
- **preStop** sleep (5–10s) + explicit `terminationGracePeriodSeconds` in `deployment.yaml`.
- **NetworkPolicy** template (default-deny + allowlist to Postgres, Redis, Keycloak, floci
  `172.18.0.1:4566`, DNS). Enforcement depends on the platform CNI.
- App code: the lifespan already disposes DB then closes cache on shutdown — verify the
  ordering lines up with the preStop drain window.

---

## Priority 3 — Data & migrations (app repo)

- Adopt **expand-contract** migration discipline in `migrations/`; document rollback
  (Atlas supports it). The db-init Helm-hook Job already exists.
- Backup/PITR engine is platform-owned (out of scope). Optionally ship PgBouncer as a
  chart dependency if you want it in the app's release.

---

## Priority 4 — Supply chain & CI (`.github/workflows/`, `Dockerfile`)

- Extend CI with gated stages: `pip-audit`/uv audit, **Trivy/Grype** image scan (fail
  HIGH/CRIT), **tfsec/checkov** on Terraform, **bandit** + CodeQL, **gitleaks**.
- **Extend the new `ecr.yml`**: generate an **SBOM** (Syft) and **sign with cosign** after
  the push. (Kyverno admission verification is platform-side.)
- **Pin the Dockerfile base by digest** — currently `FROM python:3.14-slim` (floating tag).
- **Pin GitHub Actions to commit SHAs.**

---

## Priority 5 — Observability & ops (app repo)

- App code: emit **structured audit events** (auth failure, role denial, tenant access);
  extend the existing `request_id` + `tenant_id` request logging.
- Ship **PrometheusRule** alert templates in the chart (error rate, latency, restarts,
  cert expiry, DB connections, AI spend). Grafana dashboards already live under
  `observability/`.
- Add **runbooks** to `docs/operations/` (deploy, rollback, incident, cert rotation,
  Keycloak realm recovery, migration rollback).

---

## Priority 6 — AI context (app code)

**Status: not started — no quota/circuit-breaker code in `contexts/ai/`.**

- Make the AI adapter **config-driven**: Bedrock | real Anthropic API | local Ollama/vLLM |
  deterministic mock. It's already its own bounded context, so it's a single adapter swap.
- Enforce **per-tenant token/spend quotas**, a **circuit breaker**, request timeouts, and
  a graceful fallback. Tie the per-tenant **rate-limit bucket** (Priority 1) to these
  endpoints specifically.

---

## Priority 7 — API & product hardening (app code)

- **Idempotency keys** on mutating endpoints.
- Enforced **pagination limits**, request **body-size caps**, per-request **timeouts**.
- Gate `/docs` behind auth in the prod profile (currently always mounted in `app.py`).
- Document the **API versioning / deprecation** policy.

---

## Updated status snapshot

| Item | Before | Now (`aff1cd1`) |
|------|--------|-----------------|
| Rate limiting | missing | **done (IP)** — extend to per-tenant + AI |
| CORS config | hardcoded `*` | **config-driven** — add fail-fast |
| Caching | none | **added** |
| ECR publish | none | **workflow added** — add SBOM/cosign |
| Error hygiene | leaks `str(exc)` | refactored, **still leaks** |
| Security headers | missing | **still missing** |
| OIDC/Keycloak swap | missing | **still cognito-only** |
| TLS / PDB / NetworkPolicy / startupProbe | missing | **still missing in chart** |
| AI quotas / circuit breaker | missing | **still missing** |
| Dockerfile digest pin | floating tag | **still floating** |

---

## Sequencing (each phase = PRs into this repo)

| Phase | App-repo work |
|-------|---------------|
| **0** | `OidcAuthenticator` + DI rebind + config + realm fixture + ADR-0007 |
| **1** | headers middleware · CORS fail-fast · error hygiene · per-tenant/AI rate-limit · chart TLS/WAF/rate annotations · TF cert/WAF validation |
| **2** | PDB · startupProbe · preStop · NetworkPolicy templates · lifespan drain check |
| **3** | expand-contract migrations (+ optional PgBouncer dependency) |
| **4** | CI scanning · SBOM + cosign in `ecr.yml` · pinned base/actions |
| **5** | audit events · PrometheusRule templates · runbooks |
| **6** | config-driven AI adapter + quotas/circuit breaker |
| **7** | idempotency · pagination/body/timeout limits · `/docs` gating |
