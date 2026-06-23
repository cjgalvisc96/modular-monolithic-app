# GitOps Deployment (`local-gitops`)

The service deploys **pull-based via Argo CD** onto the
[`local-gitops`](https://github.com/cjgalvisc96/local-gitops) platform — `kind`
dev/prod clusters, each running its own Argo CD as an **app-of-apps** that
recurses `platform-config/envs/<env>`, with Gitea as the in-cluster Git server,
floci as the local AWS, and the External Secrets Operator. CI builds, tests and
plans infra; it never deploys.

## The contract: self-contained app, generic platform

Everything app-specific lives **in this repo**, so onboarding the platform is a
near-zero, repeatable change — identical in shape for every future app:

| Concern | Where it lives | Files |
|---|---|---|
| Argo registration | this repo | `infra/k8s/gitops/applications/{todo-app,dependencies}-{dev,prod}.yaml` |
| API workload, IRSA SAs, RBAC, namespace, db-init | the Helm chart | `infra/k8s/helm/` |
| Local datastores (Postgres/Redis) | this repo | `infra/k8s/dependencies/base/` |
| floci SSM params + ECR repo | this repo | `infra/k8s/gitops/floci-seed.sh` |

The platform contributes only generic primitives — clusters, Argo CD, the ESO
`aws-ssm` `ClusterSecretStore`, ingress-nginx, DNS, floci, Gitea — and carries
**no `todo-app` knowledge**. Adding a second app does not touch platform code.

## Two Applications, ordered by sync-wave

Argo CD reconciles two Applications per cluster, so migrations never race an
absent database:

1. **`dependencies-<env>`** (`sync-wave: 1`) — syncs `infra/k8s/dependencies/base`
   (Postgres + Redis) and must report healthy first.
2. **`todo-app-<env>`** (`sync-wave: 2`) — syncs the Helm chart. The chart's Atlas
   migrations run as a `pre-install`/`pre-upgrade` **hook**, so they execute after
   Postgres is up but before the API rolls out.

Secrets are materialized by an `ExternalSecret` reading
`/gitops/<env>/todo-app/{DB_USER,DB_PASSWORD,REDIS_PASSWORD}` from the platform's
`aws-ssm` store (floci SSM). Ingress is `todo-app.<env>.local` on `nginx`; pods
carry Prometheus scrape annotations; the AWS SDK points at floci
(`AWS_ENDPOINT_URL=http://172.18.0.1:4566`).

## Onboarding (the minimal change on the platform)

1. **Register the repo** so the platform mirrors it and builds the image into the
   clusters:
   ```bash
   DEPLOY_APP=true APP_REPO_NAME=modular-monolithic-app \
   APP_REPO_PATH=$(pwd) APP_IMAGE=local/todo-app \
   ./install.sh            # or: task install:app
   ```
   This also runs this repo's `floci-seed.sh`. To seed floci by hand instead:
   ```bash
   task gitops:seed-floci   # → http://localhost:4566
   ```
2. **Drop the four Application manifests** into the platform control repo:
   ```bash
   cp infra/k8s/gitops/applications/*-dev.yaml   <local-gitops>/platform-config/envs/dev/
   cp infra/k8s/gitops/applications/*-prod.yaml  <local-gitops>/platform-config/envs/prod/
   ```
3. **Allow-list this repo** with one line under `sourceRepos` in each env's
   `platform-config/envs/<env>/project.yaml`.

Argo CD's `directory.recurse` discovers the rest.

## Local caveats (`kind`, not AWS)

None of these apply to a real EKS deploy:

- **IRSA annotations are no-ops** — `eks.amazonaws.com/role-arn` needs an AWS OIDC
  provider; on `kind` they are ignored.
- **AWS-backed features are inert** — Cognito, Bedrock and Aurora IAM auth have no
  local backend. Use the `DEBUG` dev-auth header and the `StubLlmClient`
  (`DEBUG=true`); `DB_*`/`REDIS_*` point at the in-namespace Postgres/Redis.
- **RLS still works** — it is pure PostgreSQL, so tenant isolation is real locally.
