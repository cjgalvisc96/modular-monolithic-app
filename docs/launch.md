# Launch

The simplest "how do I run it" guide. There are **two ways** to run this app — pick one.

## Option A — Just the app (fastest)

Run only the app and its datastores locally (no Kubernetes, no GitOps). Best for writing code and
running tests day to day.

```bash
task env:create     # one time: Python 3.14 env + dependencies + .env
task docker:up      # start everything: database, cache, migrations, seed, API
```

Open the live API docs: <http://localhost:8000/docs>

Stop it with `task docker:down`. That's all you need to develop and test.

> Under the hood `task docker:up` brings up **floci** (a fake local AWS), provisions the datastores,
> runs the migrations, seeds demo data, and starts the API — in the right order, one command.

## Option B — Full GitOps deploy (on the local lab)

Run the app the way production does: built by a pipeline and deployed by **Argo CD**, on the
[local-gitops](https://github.com/cjgalvisc96/local-gitops) lab. The **platform owns the clusters** —
`task install` creates both floci-EKS clusters (dev/prod, as k3s containers) and bootstraps each with
ingress-nginx, **Argo CD and Grafana**, so they are already running before this app deploys. This app
only provisions its own cloud resources and registers its Argo Applications onto the running clusters.

**1. Build the lab** — once, in the local-gitops repo. This brings up the dev + prod clusters with
Argo CD and Grafana already running:

```bash
cd ../local-gitops
task install
```

**2. Onboard this app** — once, back in this repo:

```bash
task gitea:create-repo      # create the app's repo in the lab's Gitea
sudo task eks:hosts         # add /etc/hosts: todo-app.dev.local → .230, todo-app.prod.local → .240
task gitea:ship             # DEV (auto): push → pipeline (ci → terraform → cd) → Argo deploys
```

`gitea:ship` pushes to the lab Gitea `main`, which fires the **DEV** pipeline. Argo CD (already
running on the dev cluster) syncs the chart.

**3. Promote to prod** — when dev looks good:

```bash
task gitea:promote          # PROD (manual): dispatch promote.yml → deploys the dev-proven tag to prod
```

**4. Iterate** — for every change:

```bash
git commit -am "my change"
task gitea:ship             # push → DEV pipeline → Argo redeploys
task gitea:runs             # see the pipeline run (or the Actions URL)
```

The app appears at <http://todo-app.dev.local> (dev, `.230`) and <http://todo-app.prod.local>
(prod, `.240`) — HTTP, not HTTPS. Argo CD and Grafana are owned by the platform.

## Start over (from scratch)

```bash
# in the local-gitops repo
task prune && task install   # rebuild both clusters + Argo + Grafana
# in this repo
task prune                   # optional: clears the Option-A standalone stack
task gitea:create-repo
task gitea:ship              # DEV
task gitea:promote           # PROD
```

## Which one should I use?

| You want to… | Use |
|---|---|
| Write code, run the API, run tests — fast | **Option A** (`task docker:up`) |
| Test the real deploy path (pipeline → Argo → cluster) | **Option B** |

More detail: [CI/CD (Gitea Actions)](operations/cicd.md) and
[GitOps Deployment](operations/gitops.md).
