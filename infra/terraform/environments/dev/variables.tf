variable "aws_region" {
  description = "AWS region for the environment."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"
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
  default     = "dev.todo-app.example.com"
}

variable "cognito_domain_prefix" {
  description = "Globally-unique Cognito hosted-UI domain prefix."
  type        = string
  default     = "todo-app-dev"
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
    "anthropic.claude-3-haiku-20240307-v1:0",
  ]
}
