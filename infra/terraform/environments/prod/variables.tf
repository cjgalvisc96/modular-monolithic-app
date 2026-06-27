variable "aws_region" {
  description = "AWS region for the environment."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "prod"
}

variable "project" {
  description = "Project name (used in tags)."
  type        = string
  default     = "todo-app"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = "platform-team"
}

variable "domain_name" {
  description = "Domain name for the hosted zone."
  type        = string
  default     = "todo-app.example.com"
}

variable "cognito_domain_prefix" {
  description = "Globally-unique Cognito hosted-UI domain prefix."
  type        = string
  default     = "todo-app-prod"
}

variable "db_master_password" {
  description = "Aurora master password. Provide via TF_VAR / secret store, never commit."
  type        = string
  sensitive   = true
}

variable "bedrock_model_ids" {
  description = "Bedrock model IDs the AI context may invoke."
  type        = list(string)
  default = [
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
  ]
}

variable "bedrock_validate_models" {
  description = "Validate Bedrock models via the foundation-model data source (real AWS). Set false on floci, which lacks the Bedrock management API."
  type        = bool
  default     = true
}

variable "floci" {
  description = "Target the local floci emulator. Disables the modules floci (LocalStack community) can't apply — aurora, redis (ElastiCache), cognito, cdn (CloudFront), route53 — so the app uses in-cluster Postgres/Redis + DEBUG dev-auth, while floci still provisions vpc/eks/ecr/iam/secrets/sqs-sns/eventbridge/s3/kms/bedrock."
  type        = bool
  default     = false
}

variable "floci_endpoint" {
  description = "floci (LocalStack) endpoint; the terragrunt-generated floci provider override targets it. Unused on real AWS."
  type        = string
  default     = "http://localhost:4566"
}
