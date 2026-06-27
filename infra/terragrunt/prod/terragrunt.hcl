# Prod environment — includes the root (DRY remote state) and points at the
# composed prod Terraform environment.

include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "${get_repo_root()}/infra/terraform//environments/prod"
}

inputs = {
  environment           = "prod"
  domain_name           = "todo-app.example.com"
  cognito_domain_prefix = "todo-app-prod"

  bedrock_model_ids = [
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
  ]

  # db_master_password is supplied via TF_VAR_db_master_password (CI secret).
}
