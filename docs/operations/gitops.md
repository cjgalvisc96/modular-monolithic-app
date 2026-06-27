# GitOps Deployment (`local-gitops`)

The service deploys **pull-based via Argo CD** onto the
[`local-gitops`](https://github.com/cjgalvisc96/local-gitops) platform — `kind`
dev/prod clusters, each running its own Argo CD as an **app-of-apps** that
recurses `platform-config/envs/<env>`, with Gitea as the in-cluster Git server,
floci as the local AWS, and the External Secrets Operator. The
[CI/CD pipeline](cicd.md) builds and pushes the image and bumps the
`values-*.yaml` tag; Argo CD reconciles that commit — it does the deploying.

## The contract: self-contained app, generic platform

Everything app-specific lives **in this repo**, so onboarding the platform is a
near-zero, repeatable change — identical in shape for every future app:

| Concern | Where it lives | Files |
|---|---|---|
| Argo registration | this repo | `infra/k8s/gitops/applications/{todo-app,dependencies}-{dev,prod}.yaml` |
| API workload, IRSA SAs, RBAC, namespace, db-init | the Helm chart | `infra/k8s/helm/` |
| Local datastores (Postgres/Redis) | this repo | `infra/k8s/dependencies/base/` |
| floci SSM params + ECR repo | this repo | `infra/terraform/local` (via the `tf-floci` pipeline / `install.sh`; `infra/k8s/gitops/floci-seed.sh` is the imperative fallback) |

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
(`AWS_ENDPOINT_URL=http://<kind-bridge-gateway>.0.1:4566` — the lab derives the
subnet prefix, so it is not always `172.18`).

## Onboarding (the app self-onboards — no platform change)

The platform installs app-agnostic; the app adds **itself** to a running lab with three one-time
tasks (see also the [Launch](../launch.md) page for the plain-words version):

```bash
task gitea:create-repo      # create gitops/modular-monolithic-app in the lab's Gitea
task argo:add-gitea-repo    # register the repo credential + apply this app's Argo
                            #   Applications (todo-app + dependencies) on dev and prod
task gitea:ship             # push the code → ci-cd.yml builds + pushes the image → Argo deploys
```

`argo:add-gitea-repo` applies the manifests in `infra/k8s/gitops/applications/` directly to each
cluster's Argo CD (`dependencies-<env>.yaml`, `todo-app-<env>.yaml`), so no copy into the platform's
`platform-config/` is needed. The floci ECR repo + SSM params are seeded by the `tf-floci` pipeline
(or `task gitops:seed-floci`). Until the first `gitea:ship`, Argo shows the app's Applications as
`Unknown`/`Failed` (empty repo) — they go green once content is shipped.

## Local caveats (`kind`, not AWS)

None of these apply to a real EKS deploy:

- **IRSA annotations are no-ops** — `eks.amazonaws.com/role-arn` needs an AWS OIDC
  provider; on `kind` they are ignored.
- **AWS-backed features are inert** — Cognito, Bedrock and Aurora IAM auth have no
  local backend. Use the `DEBUG` dev-auth header and the `StubLlmClient`
  (`DEBUG=true`); `DB_*`/`REDIS_*` point at the in-namespace Postgres/Redis.
- **RLS still works** — it is pure PostgreSQL, so tenant isolation is real locally.
