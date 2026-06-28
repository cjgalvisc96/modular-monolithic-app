# GitOps Deployment (`local-gitops`)

The service deploys **pull-based via Argo CD** onto the
[`local-gitops`](https://github.com/cjgalvisc96/local-gitops) platform. The **platform owns the
clusters**: `task install` (in the platform repo) creates both **floci-EKS** clusters — dev/prod, each
a k3s container (`floci-eks-todo-app-<env>`) that emulates EKS — and bootstraps each with MetalLB,
ingress-nginx, **Argo CD and Grafana**. So Argo CD and Grafana are already running before this app
deploys; this app does **not** create the cluster or install Argo CD. Gitea is the in-cluster Git
server, floci is the local AWS, and the External Secrets Operator is available on the platform.

This app's [CI/CD pipeline](cicd.md) provisions its own cloud resources, builds and pushes the image,
loads it into the cluster, bumps the `values-*.yaml` tag, and **registers its Argo Applications onto
the already-running cluster** (`task eks:register-app`). Argo CD then reconciles the chart — it does
the deploying.

## The contract: self-contained app, generic platform

Everything app-specific lives **in this repo**, so onboarding the platform is a
near-zero, repeatable change — identical in shape for every future app:

| Concern | Where it lives | Files |
|---|---|---|
| Argo registration | this repo | `infra/k8s/gitops/applications/{todo-app,dependencies}-{dev,prod}.yaml` (applied by the pipeline via `task eks:register-app`) |
| API workload, IRSA SAs, RBAC, namespace, db-init | the Helm chart | `infra/k8s/helm/` |
| Local datastores (Postgres/Redis) | this repo | `infra/k8s/dependencies/base/` |
| App cloud resources (ECR, SSM/Secrets, SQS/SNS, EventBridge, S3, Bedrock) | this repo | `infra/terraform/environments/{dev,prod}` — applied by the pipeline's `terraform` job (`terragrunt apply`) |

The platform contributes only generic primitives — clusters, **Argo CD and Grafana** (both already
running after `task install`), the ESO `aws-ssm` `ClusterSecretStore`, ingress-nginx, MetalLB, DNS,
floci, Gitea — and carries **no `todo-app` knowledge**. Adding a second app does not touch platform
code.

## Two Applications, ordered by sync-wave

Argo CD reconciles two Applications per cluster, so migrations never race an
absent database:

1. **`dependencies-<env>`** (`sync-wave: 1`) — syncs `infra/k8s/dependencies/base`
   (Postgres + Redis) and must report healthy first.
2. **`todo-app-<env>`** (`sync-wave: 2`) — syncs the Helm chart. The chart's Atlas
   migrations run as a `pre-install`/`pre-upgrade` **hook**, so they execute after
   Postgres is up but before the API rolls out.

On real AWS, secrets are materialized by an `ExternalSecret` reading
`/gitops/<env>/todo-app/{DB_USER,DB_PASSWORD,REDIS_PASSWORD}` from the platform's
`aws-ssm` store. On **floci** the chart uses `values-floci.yaml`, which disables
ExternalSecrets (`externalSecrets.enabled: false`) and supplies the in-cluster
Postgres/Redis credentials directly, since the app talks to the in-cluster
datastores and the AWS-backed auth path is inert. Ingress is `todo-app.<env>.local`
on `nginx` — `todo-app.dev.local` → `.230`, `todo-app.prod.local` → `.240` (HTTP, not
HTTPS); pods carry Prometheus scrape annotations.

## Onboarding (the app self-onboards — no platform change)

The platform installs app-agnostic and brings up the clusters + Argo CD + Grafana; the app then adds
**itself** to the running lab. Registration of the Argo Applications happens **inside the pipeline**
(`task eks:register-app`), so onboarding is just create-the-repo, set DNS, and ship (see also the
[Launch](../launch.md) page for the plain-words version):

```bash
task gitea:create-repo      # create gitops/modular-monolithic-app in the lab's Gitea
sudo task eks:hosts         # /etc/hosts: todo-app.dev.local → .230, todo-app.prod.local → .240
task gitea:ship             # DEV (auto): push → ci → terraform → cd (build, load, register Argo) → Argo deploys
task gitea:promote          # PROD (manual): deploy the dev-proven tag to the prod cluster
```

The `cd` job applies the manifests in `infra/k8s/gitops/applications/` directly to the running
cluster's Argo CD (`dependencies-<env>.yaml`, `todo-app-<env>.yaml`) via `task eks:register-app`, so
no copy into the platform's config is needed. The floci ECR repo + Secrets/SSM params are provisioned
by the pipeline's `terraform` job (`terragrunt apply`). `task argo:add-gitea-repo` is now just an
informational notice — the registration it used to do is done by the pipeline.

## Local caveats (floci-EKS k3s, not AWS)

None of these apply to a real EKS deploy:

- **IRSA annotations are no-ops** — `eks.amazonaws.com/role-arn` needs an AWS OIDC
  provider; on the floci-EKS k3s cluster they are ignored (and `values-floci.yaml`
  leaves the role ARNs empty).
- **AWS-backed features are inert** — Cognito, Bedrock and Aurora IAM auth have no
  local backend. Use the `DEBUG` dev-auth header (`x-dev-tenant`) and the
  `StubLlmClient` (`DEBUG=true`); `DB_*`/`REDIS_*` point at the in-cluster
  Postgres/Redis.
- **RLS still works** — it is pure PostgreSQL, so tenant isolation is real locally.
