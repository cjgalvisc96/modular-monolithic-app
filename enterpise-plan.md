# Enterprise Readiness Plan — Application Repo (AWS Production)

> **Scope:** only changes inside `cjgalvisc96/modular-monolithic-app` (the APP). The GitOps
> **platform** (`cjgalvisc96/local-gitops`) owns the EKS cluster wiring, Argo CD, Grafana, External
> Secrets Operator (ESO), and the CloudWatch sink. This app is **deployed onto** that platform.
>
> **Target:** a full **production deployment on a real AWS account** — real Amazon Cognito, Aurora,
> ElastiCache, ACM/CloudFront/WAF, Secrets Manager/SSM/KMS, SQS/SNS/EventBridge, ECR, S3, Bedrock,
> DynamoDB, CloudWatch, all behind least-privilege IAM via IRSA. The Terraform stack under
> `infra/terraform/` **is** that production stack.
>
> **Local development (floci):** floci (LocalStack at `http://localhost:4566`) is *only* the local
> inner-loop dev/CI emulator. `var.floci=true` gates off the services LocalStack-community can't run
> (vpc/eks, aurora, redis, cognito, cdn, route53, IRSA-iam) so the inner loop runs against
> in-cluster Postgres/Redis and the DEBUG dev-auth path. **Everything in this plan is built for real
> AWS;** floci is the dev shim, not the design target.

---

## Production AWS stack (grounding)

`infra/terraform/environments/{dev,prod}/main.tf` provisions the real production stack. The modules
marked *local-gated* below are `count = var.floci ? 0 : 1` — present and applied on **real AWS**,
substituted by an in-cluster shim only for local floci runs:

| Module | Prod (real AWS) | Local (floci) |
|--------|:---------------:|---------------|
| `vpc`, `eks` | **real** (Multi-AZ, IRSA) | platform k3s; gated off |
| `aurora` | **real** (Multi-AZ, PITR, KMS) | in-cluster Postgres pod; gated off |
| `redis` (ElastiCache) | **real** | in-cluster Redis pod; gated off |
| `cognito` | **real** user pool | DEBUG `x-dev-tenant`; gated off |
| `cdn` (CloudFront), `route53`, `iam` (IRSA) | **real** | gated off |
| `ecr`, `secrets-manager`, `eventbridge`, `sqs-sns`, `bedrock`, `s3_assets` | **real** | run on floci too |

`.gitea/workflows/ci-cd.yml` → `ci` (lint/types/deadcode/architecture/coverage≥97) → `terraform`
(fmt/validate/**trivy**/terragrunt apply, state in S3) → `cd` (build prod image, push to ECR,
`eks:load-image`, bump `values-dev.yaml`, `eks:register-app`). `.gitea/workflows/promote.yml` is the
manual prod gate (same shape, `ENV=prod`).

---

## ✅ Landed / status snapshot

| Item | Status | Remaining |
|------|--------|-----------|
| Rate limiting | **done (IP-only)** `presentation/api/middleware/rate_limit.py`, Redis fixed-window, fail-open | add **per-tenant** key + stricter **`/api/v1/ai/*`** bucket (P5) |
| CORS | **config-driven** `core/config.py` `cors_origin_list` | still defaults `*` + credentials → add **fail-fast** validator (P3) |
| Caching | **added** `shared/infrastructure/cache/redis_cache.py` | tenant-scoped cache-key hygiene only |
| ECR publish | **in `cd`** (immutable tags) | add **scan-on-push + Trivy + Syft SBOM + cosign sign** (P4) |
| Terraform Trivy | **done** `task terraform:trivy` (ci-cd + promote) | extend to image layer (P4) |
| Terraform stack | **modules exist** (vpc/eks/aurora/redis/cognito/ecr/secrets/sqs-sns/eventbridge/s3/cdn/route53/iam/bedrock) | add **WAF** + ACM/TLS-min validation (P3) |
| Cognito auth | **`CognitoAuthenticator` exists** + DEBUG dev-auth (`x-dev-tenant`) | config-driven **OIDC via SSM**; enable MFA/advanced security (P1) |
| Secrets | **`externalsecret.yaml` template exists** | wire **ESO + IRSA** end-to-end; drop inlined creds outside local (P2) |
| Error hygiene | **refactored** `errors.py` (status-map) | **still returns `str(exc)`** → stop leaking (P3) |
| Security headers | **missing** | add middleware (P3) |
| TLS / PDB / NetworkPolicy / startupProbe / preStop | **missing in chart** | add (P3/P4) |
| AI quotas / circuit breaker | **missing** (`contexts/ai/`) | config-driven adapter + quotas (P6) |
| Domain events | SQS/SNS/EventBridge **provisioned but unconsumed** | publish from tasks/ai (P5) |
| Dockerfile base | **floating** `FROM python:3.14-slim` | pin by **digest** (P4) |

---

## Prerequisites owned by `local-gitops` (out of scope)

The **EKS cluster** bootstrap, **Argo CD** + the `eks:register-app` / `eks:load-image` tasks,
**Grafana**, the **External Secrets Operator** + its AWS `ClusterSecretStore`, the **CloudWatch** log
sink, ingress-nginx, and the CNI that enforces `NetworkPolicy`. The app chart only *references*
these.

---

## Priority 1 — Identity: real Amazon Cognito, config-driven OIDC

**Status: `CognitoAuthenticator` is the only authenticator; issuer/JWKS are derived from
`region`+`user_pool_id`.** Files: `contexts/users/infrastructure/auth/cognito.py`,
`presentation/api/dependencies.py`, `core/config.py`. AWS service: **Amazon Cognito**.

- **Keep `CognitoAuthenticator`** (RS256/JWKS, audience + issuer validation already enforced). In
  production enable Cognito **MFA** and **advanced security** (compromised-credential / risk-based)
  on the user pool (`infra/terraform/modules/cognito/`).
- Make the verifier **config-driven**: read `oidc_issuer`, `oidc_jwks_url`, `oidc_audience` from
  `core/config.py` instead of computing them from `cognito_*`, so the issuer/JWKS/audience are
  injected from **SSM** (via ESO → ConfigMap) rather than hardcoded. Token validation logic is
  unchanged.
- **DEBUG `x-dev-tenant` / `x-dev-roles` stays ONLY as the local floci fallback** — it is
  `settings.debug` gated in `dependencies.py` and is never reachable in prod (debug off).
- **ADR-0007:** record real-Cognito-in-prod + the config-driven OIDC inputs.

---

## Priority 2 — Secrets & config: Secrets Manager + SSM + KMS via ESO/IRSA

**Status: the chart has `templates/externalsecret.yaml`, but `values-floci.yaml` inlines
`DB_USER/DB_PASSWORD/REDIS_PASSWORD` for local.** AWS services: **Secrets Manager + SSM Parameter
Store + KMS**, surfaced through **External Secrets Operator** with **IRSA**.

- In production, the app reads **real secrets**: DB credentials from **Secrets Manager** and the
  OIDC config (P1) from **SSM**, both **KMS-encrypted**, materialized into the app Secret by ESO
  against the cluster `ClusterSecretStore`. The API pod's **IRSA** role grants read on exactly the
  scoped secret ARNs (`infra/terraform/modules/iam/api_pod_role.tf`).
- **No creds in `values-prod.yaml`** — `externalSecrets.enabled: true` for dev/prod;
  `values-floci.yaml` keeps inlined creds **only** for the local loop.

---

## Priority 3 — Edge security, TLS & WAF

AWS services: **ACM** (cert), **CloudFront**, **AWS WAF**. Files: `presentation/api/`,
`infra/k8s/helm/`, `infra/terraform/`.

### App code
- **Security headers middleware** — HSTS, `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy`, CSP (allow `/docs` + `/redoc`); register in
  `ApiBuilder._configure_middleware`. *Not present today.*
- **CORS fail-fast** — `core/config.py` validator: refuse to start when `debug=false` **and**
  `cors_allow_origins="*"` **and** `cors_allow_credentials=true`. Require an explicit allowlist.
- **Error hygiene** (`errors.py`) — stop returning `str(exc)`; return a generic body + the existing
  `x-request-id`, log the detail server-side. *Currently still leaks.*

### Edge (Terraform + chart)
- **ACM cert + CloudFront + AWS WAF** in front of the app: add a **WAF** web ACL (managed rule
  groups, rate-based rules) and associate it with CloudFront / the ALB. The `cdn` and `route53`
  modules already exist; **add a WAF module** and require `web_acl_id` in prod via variable
  validation.
- Require `acm_certificate_arn` in prod; pin TLS **`TLSv1.2_2021`** as the minimum on CloudFront /
  the ingress.
- **Ingress TLS** on `ingress.yaml` (ACM-backed) with `force-ssl-redirect` true in `values-prod.yaml`.

---

## Priority 4 — Resilience & supply chain

### Resilience (`infra/k8s/helm/`)
- **HPA** — already templated (`templates/hpa.yaml`); confirm CPU/mem targets and min/max for prod.
- **PodDisruptionBudget** (`minAvailable: 2` prod), **startupProbe** on `/health` decoupled from
  liveness, **preStop** sleep (5–10s) + `terminationGracePeriodSeconds` in `deployment.yaml`.
- **NetworkPolicy** (default-deny + allowlist to Aurora, ElastiCache, AWS endpoints, DNS).
- **Multi-AZ** across the board: EKS node groups, Aurora, ElastiCache (P5 data) span ≥2 AZs.

### Supply chain (`.gitea/workflows/`, `Dockerfile`)
- Enable **ECR scan-on-push** (`infra/terraform/modules/ecr/`). In `cd`, after the push:
  **Trivy/Grype** image scan (fail HIGH/CRIT), **Syft SBOM**, **cosign sign**.
- Extend `ci` with `pip-audit`/uv audit, **bandit**, **gitleaks**.
- **Pin the Dockerfile base by digest** — `FROM python:3.14-slim` → `…@sha256:…` across all four
  stages (`base`/`builder`/`dev`/`prod`).
- **Pin Actions to commit SHAs** (`actions/checkout`, the `setup-lab` action).

---

## Priority 5 — Data, messaging & rate limiting

### Data — **Aurora (Multi-AZ, PITR, KMS) + ElastiCache**
- The `aurora` module backs prod Postgres; confirm **Multi-AZ**, **PITR/automated backups**, and
  **KMS** storage encryption. ElastiCache (`redis` module) backs the cache/rate-limit store.
- Adopt **expand-contract** migration discipline; the db-init Helm-hook Job already exists. Document
  rollback.
- **DynamoDB for idempotency keys** on mutating endpoints (new module + adapter behind a port).

### Messaging — **SQS / SNS / EventBridge**
- **Consume the real messaging the terraform provisions** (`sqs-sns` → `${name}-tasks`,
  `eventbridge` → `${name}-events`), currently created but **unconsumed**. Publish **domain events**
  from the `tasks` and `ai` contexts (task-created, suggestion-ready) via an infrastructure adapter
  behind a domain port — boto3 stays out of domain/application.

### Rate limiting
- Extend `rate_limit.py` (IP-only today) with a **per-tenant** dimension and a **stricter
  `/api/v1/ai/*` bucket** (tied to P6 quotas). Keep the documented fail-open behavior.

---

## Priority 6 — AI context (real Bedrock + quotas)

AWS service: **Amazon Bedrock**. Files: `contexts/ai/`.

- The adapter is **already config-driven**: `ai/container.py::_build_llm_client(debug, region)`
  selects `StubLlmClient` locally and **`BedrockLlmClient`** on real AWS. Keep the `LlmClient` port
  as the only seam; **boto3/Bedrock stays in `ai/infrastructure/bedrock/bedrock_client.py`** only,
  invoked under the AI pod's scoped IRSA role (`bedrock:InvokeModel` on specific ARNs).
- Add **per-tenant token/spend quotas**, a **circuit breaker**, request timeouts, and graceful
  fallback on breaker-open. Persist quota/spend counters in **DynamoDB**.

---

## Priority 7 — Storage, observability & API hardening

### Storage — **S3**
- Route **static assets / task exports** through an S3 adapter (behind a port). CloudFront (P3)
  fronts the bucket.

### Observability — **CloudWatch**
- Ship **audit + app logs to CloudWatch Logs**: emit **structured audit events** (auth failure, role
  denial, tenant access) extending the existing `request_id` + `tenant_id` logging.
- Ship **PrometheusRule** alert templates in the chart (error rate, latency, restarts, DB
  connections, AI spend, cert expiry) — Grafana is platform-owned.
- Add runbooks under `docs/operations/` (deploy, rollback, incident, cert rotation, migration
  rollback).

### API hardening
- Enforce **pagination limits**, request **body-size caps**, per-request **timeouts**; gate `/docs`
  behind auth in the prod profile; document the API versioning/deprecation policy.

---

## Sequencing (each phase = PRs into this repo)

| Phase | App-repo work | Primary AWS service |
|-------|---------------|---------------------|
| **1** | config-driven OIDC inputs · Cognito MFA/advanced security · ADR-0007 · keep local dev-auth | Cognito + SSM |
| **2** | ESO + IRSA secrets end-to-end · drop inlined creds outside `values-floci.yaml` | Secrets Manager + SSM + KMS |
| **3** | headers middleware · CORS fail-fast · error hygiene · ACM/CloudFront/**WAF** · ingress TLS · TF WAF/ACM/TLS-min validation | ACM / CloudFront / WAF |
| **4** | PDB · NetworkPolicy · startupProbe · preStop · HPA tuning · ECR scan-on-push · Trivy + Syft + cosign · pin base digest + actions | ECR |
| **5** | Aurora Multi-AZ/PITR/KMS check · ElastiCache · expand-contract migrations · DynamoDB idempotency · consume SQS/SNS/EventBridge · per-tenant + AI rate-limit | Aurora / ElastiCache / SQS/SNS/EventBridge / DynamoDB |
| **6** | Bedrock quotas · circuit breaker · DynamoDB counters | Bedrock + DynamoDB |
| **7** | S3 asset/export adapter · CloudWatch audit logs · PrometheusRule · API caps · `/docs` gating | S3 / CloudWatch |

See `docs/architecture/` and `docs/adr/` for the rationale behind each rule.
