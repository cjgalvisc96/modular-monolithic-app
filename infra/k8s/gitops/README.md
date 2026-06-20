# GitOps — todo-app

This directory wires the `todo-app` Helm chart (`infra/k8s/helm`) into a GitOps
delivery flow driven by [Argo CD], and integrates with the local multi-cluster
simulator at <https://github.com/cjgalvisc96/local-gitops>.

[Argo CD]: https://argo-cd.readthedocs.io/

## Topology

`local-gitops` boots two independent Kubernetes clusters (e.g. two `kind` /
`k3d` clusters) to emulate a real promotion path:

| Cluster        | Namespace  | Values file        | Argo CD Application |
| -------------- | ---------- | ------------------ | ------------------- |
| `dev-cluster`  | `dev-app`  | `values-dev.yaml`  | `app-dev.yaml`      |
| `prod-cluster` | `prod-app` | `values-prod.yaml` | `app-prod.yaml`     |

Each cluster is fully isolated: separate API servers, separate namespaces,
separate per-namespace RBAC (`Role` + `RoleBinding` rendered by the chart), and
separate IRSA role ARNs per workload. Nothing crosses the dev/prod boundary.

```
                       ┌──────────────────────────────┐
                       │  local-gitops (Argo CD host)  │
                       │        namespace: argocd       │
                       └───────────────┬───────────────┘
                       app-dev.yaml    │   app-prod.yaml
              ┌─────────────────────────┴─────────────────────────┐
              ▼                                                   ▼
   ┌────────────────────┐                            ┌────────────────────┐
   │    dev-cluster      │                            │    prod-cluster     │
   │  ns: dev-app        │                            │  ns: prod-app       │
   │  values-dev.yaml    │                            │  values-prod.yaml   │
   │  HPA off, 1 replica │                            │  HPA on, 3-10 reps  │
   └────────────────────┘                            └────────────────────┘
```

## Argo CD Application flow

Both `app-dev.yaml` and `app-prod.yaml` are Argo CD `Application` resources
applied to the Argo CD control plane (`namespace: argocd`). Each one:

1. **Source** — points at the chart path `infra/k8s/helm` in the
   `local-gitops` repo (this repository's `infra/k8s` tree is vendored /
   submoduled there), pinned to `targetRevision: main`.
2. **Helm values** — layers `values.yaml` then the env-specific overrides
   (`values-dev.yaml` / `values-prod.yaml`), so the same chart renders two
   different shapes.
3. **Destination** — targets a named cluster (`dev-cluster` / `prod-cluster`)
   and namespace (`dev-app` / `prod-app`).
4. **Sync policy** —
   - dev: fully automated (`prune: true`, `selfHeal: true`,
     `CreateNamespace=true`) for fast iteration.
   - prod: `selfHeal: true` but `prune: false` so destructive changes are
     promoted deliberately; the namespace is platform-managed.

### Helm hooks under Argo CD

The chart ships the Atlas migration Job as a Helm `pre-install,pre-upgrade`
hook. Argo CD understands Helm hooks and maps them onto its own
`PreSync` phase, so the **DB-init Job runs to completion before the API
Deployment is synced** — preserving the "migrate first, then roll the API"
guarantee without coupling migrations to the API container.

## App-of-Apps (optional)

To manage both environments from one root, register an `Application` whose
source is this `gitops/` directory; Argo CD then adopts `app-dev.yaml` and
`app-prod.yaml` as children (the classic *app-of-apps* pattern). The
`local-gitops` repo's root application can reference this directory directly.

## Promotion

1. Merge a change to the chart / `values-dev.yaml` → Argo CD auto-syncs
   `dev-cluster`.
2. Validate in `dev-app`.
3. Promote by updating `values-prod.yaml` (or bumping `image.tag`) → Argo CD
   syncs `prod-cluster` (self-heal on, manual prune).

## Local quick start

```bash
# 1. Bring up the two clusters + Argo CD (see local-gitops README).
git clone https://github.com/cjgalvisc96/local-gitops.git
cd local-gitops && make up        # boots dev-cluster, prod-cluster, argocd

# 2. Register the Applications.
kubectl apply -f infra/k8s/gitops/app-dev.yaml
kubectl apply -f infra/k8s/gitops/app-prod.yaml

# 3. Watch them sync.
argocd app list
argocd app get todo-app-dev
```
