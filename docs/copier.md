# Copier Template

This repository doubles as a [Copier](https://copier.readthedocs.io/) template: a new
DDD modular-monolith service can be scaffolded from it, with answer-driven toggles for the
optional pieces (AI context, RLS, Kubernetes, Terraform, observability, CLI, tooling).

`copier.yml` lives at the repo root (so `copier copy gh:org/repo` resolves it); everything else is
tidied under **`copier/`** (`_subdirectory: copier/template`):

```
copier.yml              questionnaire + settings (_subdirectory: copier/template)
copier/
├── includes/           Jinja partials — slug, module name, image name (DRY derived values)
├── tasks/              post-generation scripts (tool check, migrations)
└── template/           the renderable app tree
```

## Questionnaire

Defaults reproduce the full reference app — press Enter through everything to get the complete
architecture.

| Group | Questions |
|-------|-----------|
| Identity | `project_name`, `project_slug` (derived), `module_name` (derived), `author_*`, `python_version`, `owner` |
| Contexts | `bounded_contexts` (users + tasks mandatory; `ai` opt-out) |
| Auth & tenancy | `auth_provider` (cognito), `enable_rls` |
| Infrastructure | `include_docker`, `include_k8s`, `include_terraform`, `cloud_modules`, `include_observability` |
| Tooling | `include_cli`, `include_governance`, `coverage_threshold`, `include_mkdocs`, `include_agents`, `include_claude` |

`project_slug` and `module_name` are **derived** from `project_name` via `includes/` partials (DRY);
`bedrock` in `cloud_modules` is rejected unless the `ai` context is selected.

## Generate a project

The template uses Jinja extensions + post-generation tasks, so it is "unsafe" by Copier's
definition — pass `--trust`:

```bash
uv tool install --with copier-templates-extensions --with jinja2-time copier
copier copy --trust gh:<org>/<repo> path/to/my-service
```

Answers persist in the generated project's `.copier-answers.yml`, so `copier update --trust` pulls
later template improvements while preserving local code and answers.
