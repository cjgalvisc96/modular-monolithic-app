# Local-only Terraform stack targeting floci (the local AWS emulator). It stands
# in for the cloud dev/prod stacks during the docker-compose flow, provisioning
# ONLY the AWS resources floci can emulate: the ECR repo + the SSM parameters the
# app / GitOps ExternalSecret consume. The managed control-plane services the
# real stacks create (VPC, EKS, Aurora, ElastiCache, CloudFront, Cognito,
# Route53) cannot run on floci and are intentionally absent here.
#
# Resources are kept minimal (no KMS/lifecycle/encryption hardening) for floci
# API compatibility; this stack is excluded from the Trivy IaC gate for that
# reason (see `task terraform:trivy`).

provider "aws" {
  region     = var.region
  access_key = "test"
  secret_key = "test"

  # floci is not real AWS — skip every call the provider would make to the real
  # metadata / IAM / STS endpoints, and route the service APIs at floci.
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  s3_use_path_style           = true

  endpoints {
    ecr = var.floci_endpoint
    ssm = var.floci_endpoint
    sts = var.floci_endpoint
    iam = var.floci_endpoint
    s3  = var.floci_endpoint
  }
}

# --- ECR: the app image registry ------------------------------------------
resource "aws_ecr_repository" "app" {
  name                 = var.repository_name
  image_tag_mutability = "MUTABLE" # local: allow re-pushing the same tag
  force_delete         = true      # local: destroy even with images present
}

# --- SSM: secrets the app / GitOps consume (/gitops/<env>/todo-app/*) ------
locals {
  ssm_params = merge([
    for env in var.environments : {
      "/gitops/${env}/todo-app/DB_USER"        = { value = "todo", type = "String" }
      "/gitops/${env}/todo-app/DB_PASSWORD"    = { value = "todo", type = "SecureString" }
      "/gitops/${env}/todo-app/REDIS_PASSWORD" = { value = "redispass", type = "SecureString" }
    }
  ]...)
}

resource "aws_ssm_parameter" "todo_app" {
  for_each  = local.ssm_params
  name      = each.key
  type      = each.value.type
  value     = each.value.value
  overwrite = true
}
