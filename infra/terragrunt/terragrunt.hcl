# Root Terragrunt configuration — DRY remote state, provider generation and
# common inputs shared by every environment. Child configs `include` this.

locals {
  project    = "todo-app"
  aws_region = "us-east-1"
  owner      = "platform-team"

  # Each child sets `environment` in its inputs; default to the dir name.
  env = basename(get_terragrunt_dir())
}

# Remote state: versioned, encrypted S3 bucket + DynamoDB lock table.
remote_state {
  backend = "s3"

  generate = {
    path      = "backend_generated.tf"
    if_exists = "overwrite_terragrunt"
  }

  config = {
    bucket         = "${local.project}-tfstate-${local.env}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.aws_region
    encrypt        = true
    dynamodb_table = "${local.project}-tflock-${local.env}"

    s3_bucket_tags = {
      Project   = local.project
      ManagedBy = "terragrunt"
    }
  }
}

# Generate the AWS provider block so the environments don't each duplicate it.
generate "provider" {
  path      = "provider_generated.tf"
  if_exists = "overwrite_terragrunt"

  contents = <<-EOF
    provider "aws" {
      region = "${local.aws_region}"

      default_tags {
        tags = {
          Project   = "${local.project}"
          ManagedBy = "terragrunt"
        }
      }
    }

    # us-east-1 alias for CloudFront ACM certificates.
    provider "aws" {
      alias  = "us_east_1"
      region = "us-east-1"
    }
  EOF
}

# Common inputs merged into every environment.
inputs = {
  aws_region = local.aws_region
  project    = local.project
  owner      = local.owner
}
