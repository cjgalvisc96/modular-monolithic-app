# copier-todo-ddd

A [Copier](https://copier.readthedocs.io/) template that scaffolds a DDD modular-monolith
service from this reference application, with answer-driven toggles for the AI context, RLS
multi-tenancy, Kubernetes, Terraform, observability, CLI, and tooling.

`copier.yml` lives at the repo root; this `copier/` folder holds the rest of the template
(`_subdirectory: copier/template`).

## Layout

```
copier.yml              questionnaire + settings
copier/
├── includes/           Jinja partials for derived values (slug, module name, image name)
├── tasks/              post-generation scripts (check_tools.sh, post_gen.py)
└── template/           the renderable app tree
```

## Use it

The template uses Jinja extensions and post-generation tasks, so it is "unsafe" by Copier's
definition — consumers pass `--trust`.

```bash
uv tool install --with copier-templates-extensions --with jinja2-time copier

copier copy --trust gh:<org>/<repo> path/to/my-service
cd path/to/my-service && uv sync && task help
```

Later, pull template improvements (answers persist in the generated `.copier-answers.yml`):

```bash
copier update --trust
```
