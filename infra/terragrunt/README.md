# Terragrunt — DRY environment orchestration

Terragrunt wraps the Terraform in `infra/terraform/environments/<env>` to provide
**DRY remote state**, **provider generation**, and **shared inputs** across the
`dev` and `prod` environments.

## Layout

```
infra/terragrunt/
  terragrunt.hcl      # root: remote_state (S3 + DynamoDB lock), provider gen, common inputs
  dev/terragrunt.hcl  # includes root, source = environments/dev, dev inputs
  prod/terragrunt.hcl # includes root, source = environments/prod, prod inputs
```

## How DRY composition works

- **`remote_state`** in the root defines an S3 backend (`<project>-tfstate-<env>`)
  with a DynamoDB lock table (`<project>-tflock-<env>`). Each child inherits it via
  `include "root"`; the state `key` is derived from `path_relative_to_include()`,
  so every environment lands in its own state file automatically.
- **`generate "provider"`** in the root can emit a provider block. The composed
  environments already ship their own `provider "aws"` blocks (so they also work
  with plain `terraform`), so each child overrides the generate block with
  `if_exists = "skip"` to avoid a duplicate-provider definition.
- **`inputs`** in the root carry common values (`aws_region`, `project`, `owner`);
  each child adds environment-specific values (`environment`, `domain_name`,
  `cognito_domain_prefix`, `bedrock_model_ids`). Terragrunt deep-merges them.

## Running

Secrets are never committed. Export the DB master password first:

```bash
export TF_VAR_db_master_password='...'   # from your secret store / CI secret
```

Per environment:

```bash
# Dev
cd infra/terragrunt/dev
terragrunt init
terragrunt plan
terragrunt apply

# Prod
cd infra/terragrunt/prod
terragrunt plan
terragrunt apply
```

Run-all across every environment from the root:

```bash
cd infra/terragrunt
terragrunt run-all plan
terragrunt run-all apply
```

> The remote-state S3 bucket and DynamoDB lock table are created automatically by
> Terragrunt on first `init` if they do not already exist.
