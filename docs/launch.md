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
[local-gitops](https://github.com/cjgalvisc96/local-gitops) lab.

**1. Build the lab** — once, in the local-gitops repo:

```bash
cd ../local-gitops
task install
```

**2. Onboard this app** — once, back in this repo:

```bash
task gitea:create-repo      # create the app's repo in the lab's Gitea
task argo:add-gitea-repo    # register it with Argo CD (dev + prod) and apply its Applications
task gitea:ship             # push the code → pipeline builds + pushes the image → Argo deploys
```

**3. Iterate** — for every change:

```bash
git commit -am "my change"
task gitea:ship             # push → pipeline → Argo redeploys
task gitea:runs             # see the pipeline run (or the Actions URL)
```

The app appears at <http://todo-app.dev.local>.

## Start over (from scratch)

```bash
# in the local-gitops repo
task prune && task install
# in this repo
task prune                  # optional: clears the Option-A standalone stack
task gitea:create-repo
task argo:add-gitea-repo
task gitea:ship
```

## Which one should I use?

| You want to… | Use |
|---|---|
| Write code, run the API, run tests — fast | **Option A** (`task docker:up`) |
| Test the real deploy path (pipeline → Argo → cluster) | **Option B** |

More detail: [CI/CD (Gitea Actions)](operations/cicd.md) and
[GitOps Deployment](operations/gitops.md).
