# Root Terragrunt configuration — DRY remote state, provider generation and
# common inputs shared by every environment. Child configs `include` this.
#
# FLOCI mode: set FLOCI=true (and optionally FLOCI_ENDPOINT) to target the local
# floci emulator instead of real AWS. That switches the backend to a local state
# file, generates a floci endpoints override for the provider, and tells the env
# to disable the modules floci can't apply (var.floci / bedrock_validate_models).

locals {
  project    = "todo-app"
  aws_region = "us-east-1"
  owner      = "platform-team"

  # Each child sets `environment` in its inputs; default to the dir name.
  env = basename(get_terragrunt_dir())

  floci          = lower(get_env("FLOCI", "false")) == "true"
  floci_endpoint = get_env("FLOCI_ENDPOINT", "http://localhost:4566")

  # floci endpoints map (one URL for every service the env stack touches),
  # pre-rendered to a string so the generated provider has no inline templating.
  floci_services = [
    "ec2", "eks", "ecr", "rds", "elasticache", "cognitoidp", "cognitoidentity",
    "secretsmanager", "iam", "sts", "s3", "sns", "sqs", "events", "scheduler",
    "cloudfront", "route53", "acm", "kms", "lambda", "cloudwatch", "logs", "bedrock",
  ]
  floci_endpoints_block = join("\n", [for s in local.floci_services : "        ${s} = \"${local.floci_endpoint}\""])

  # The floci provider override, as a string (heredoc can't sit inside a ternary).
  floci_provider_contents = <<-EOT
    provider "aws" {
      region                      = "${local.aws_region}"
      access_key                  = "test"
      secret_key                  = "test"
      skip_credentials_validation = true
      skip_metadata_api_check     = true
      skip_requesting_account_id  = true
      skip_region_validation      = true
      s3_use_path_style           = true
      endpoints {
${local.floci_endpoints_block}
      }
    }
    provider "aws" {
      alias                       = "us_east_1"
      region                      = "us-east-1"
      access_key                  = "test"
      secret_key                  = "test"
      skip_credentials_validation = true
      skip_metadata_api_check     = true
      skip_requesting_account_id  = true
      skip_region_validation      = true
      s3_use_path_style           = true
      endpoints {
        cloudfront = "${local.floci_endpoint}"
        acm        = "${local.floci_endpoint}"
        route53    = "${local.floci_endpoint}"
        s3         = "${local.floci_endpoint}"
      }
    }
  EOT
}

# Remote state: real AWS uses a versioned, encrypted S3 bucket + DynamoDB lock.
# floci uses a local state file (the ci-cd/promote pipelines sync it to/from
# floci S3 between runs) — terragrunt's S3 backend bootstrap doesn't honour
# custom endpoints, so a local backend is the reliable choice for floci.
remote_state {
  backend = local.floci ? "local" : "s3"

  # Overwrite the env's placeholder backend.tf in the cache so terragrunt owns
  # the backend (local for floci, s3 for real AWS) — generating a *second*
  # backend file would collide with that placeholder.
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }

  # The local and s3 backends take differently-shaped config maps; an HCL ternary
  # rejects mismatched object types, so round-trip each branch through JSON.
  config = jsondecode(local.floci ? jsonencode({
    path = "${get_repo_root()}/infra/terraform/.floci-state/${local.env}/terraform.tfstate"
    }) : jsonencode({
    bucket         = "${local.project}-tfstate-${local.env}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.aws_region
    encrypt        = true
    dynamodb_table = "${local.project}-tflock-${local.env}"
    s3_bucket_tags = {
      Project   = local.project
      ManagedBy = "terragrunt"
    }
  }))
}

# Note: each environment declares its own `provider "aws"` blocks in main.tf (so
# the stacks stay usable with plain `terraform` too), so the root generates no
# real-AWS provider — that would duplicate them. floci is handled by the
# *_override.tf below, which merges over those blocks.

# floci endpoints override — generated ONLY when FLOCI=true. As an *_override.tf
# it merges over the env's own `provider "aws"` blocks, repointing them at floci.
generate "floci_provider" {
  path      = "zz_floci_override.tf"
  if_exists = "overwrite_terragrunt"

  contents = local.floci ? local.floci_provider_contents : "# FLOCI=false: real-AWS provider from environments/<env>/main.tf is used."
}

# Common inputs merged into every environment.
inputs = {
  aws_region              = local.aws_region
  project                 = local.project
  owner                   = local.owner
  floci                   = local.floci
  floci_endpoint          = local.floci_endpoint
  bedrock_validate_models = !local.floci
}
