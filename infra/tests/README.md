# floci — infra unit-testing layer

`floci` is the **infra-as-code testing layer** for `todo-app`. It treats the
Helm chart and Kubernetes manifests as code and runs two complementary kinds of
checks before anything reaches a cluster:

| Layer        | Tool                          | What it verifies                                        |
| ------------ | ----------------------------- | ------------------------------------------------------- |
| Unit / shape | [Terratest] (Go)              | The chart renders the *right* objects with the *right* shape (Deployment, IRSA SAs, DB-init pre-install hook). |
| Security     | [Trivy] (`config`/misconfig)  | The rendered manifests have no HIGH/CRITICAL misconfigurations. |

[Terratest]: https://terratest.gruntwork.io/
[Trivy]: https://trivy.dev/

## 1. Terratest (`terratest/`)

`helm_chart_test.go` uses `helm.RenderTemplate` to render the chart **without a
live cluster** and asserts the architectural invariants:

- `TestDeploymentRendered` — the API Deployment exists, runs
  `local/todo-app:*` on container port `8000`, and has readiness/liveness
  probes on `/health`, using the API ServiceAccount.
- `TestServiceAccountsHaveIRSA` — the `api`, `ai` and `db-init` ServiceAccounts
  each carry their own `eks.amazonaws.com/role-arn` annotation and the three
  ARNs are **distinct** (no shared role).
- `TestDBInitJobIsPreInstallHook` — the Atlas migration Job is a Helm
  `pre-install,pre-upgrade` hook with a hook-weight + hook-delete-policy, runs
  `atlas migrate apply`, and uses the db-init ServiceAccount.
- `TestDeploymentHasNoMigrationContainer` — the API Deployment does **not**
  embed Atlas, proving migrations are decoupled from the API container.

### Run

```bash
cd infra/tests/terratest
go mod download
go test -v ./...
```

Requires Go 1.22+ and the `helm` binary on `PATH` (Terratest shells out to it).

## 2. Trivy (`trivy/`)

`trivy-config.yaml` configures a misconfiguration scan over the chart, gated at
`HIGH,CRITICAL`. `.trivyignore` documents every accepted exception.

### Run

```bash
# from the repo root
trivy config --config infra/tests/trivy/trivy-config.yaml infra/k8s

# or scan a fully rendered manifest
helm template todo-app infra/k8s/helm -f infra/k8s/helm/values-prod.yaml > /tmp/rendered.yaml
trivy config --config infra/tests/trivy/trivy-config.yaml /tmp/rendered.yaml
```

A non-zero exit code means a HIGH/CRITICAL misconfiguration was found.

## CI wiring (suggested)

```yaml
# pseudo-pipeline
- helm lint infra/k8s/helm
- (cd infra/tests/terratest && go test ./...)
- trivy config --config infra/tests/trivy/trivy-config.yaml infra/k8s
```
