variable "name" {
  description = "Name prefix for the IAM roles."
  type        = string
  default     = "todo-app"
}

############################################
# IRSA trust inputs — from the EKS module
############################################
variable "oidc_provider_arn" {
  description = "ARN of the EKS cluster IAM OIDC provider."
  type        = string
}

variable "oidc_provider_url" {
  description = "URL of the EKS cluster OIDC issuer WITHOUT the https:// scheme (e.g. oidc.eks.us-east-1.amazonaws.com/id/ABC...)."
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace the workloads run in (app-named, e.g. todo-app)."
  type        = string
}

variable "api_service_account_name" {
  description = "Service account name for the API pod."
  type        = string
  default     = "todo-app-api"
}

variable "ai_service_account_name" {
  description = "Service account name for the AI pod."
  type        = string
  default     = "todo-app-ai"
}

variable "db_init_service_account_name" {
  description = "Service account name for the DB-init Job."
  type        = string
  default     = "todo-app-db-init"
}

############################################
# Resource scopes for least-privilege policies
############################################
variable "aurora_cluster_resource_id" {
  description = "Aurora cluster resource ID used to build the rds-db:connect ARN."
  type        = string
}

variable "db_iam_username" {
  description = "Database username the API authenticates as via IAM auth (rds-db:connect target)."
  type        = string
  default     = "todo_app"
}

variable "db_init_iam_username" {
  description = "Database username the DB-init Job authenticates as via IAM auth."
  type        = string
  default     = "todo_migrator"
}

variable "aws_region" {
  description = "AWS region (used to build rds-db ARNs)."
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID (used to build rds-db ARNs)."
  type        = string
}

variable "api_secret_arns" {
  description = "Secrets Manager ARNs the API pod may read (its DB + Cognito secrets ONLY)."
  type        = list(string)
}

variable "db_init_secret_arns" {
  description = "Secrets Manager ARNs the DB-init Job may read (its migration creds ONLY)."
  type        = list(string)
}

variable "bedrock_model_arns" {
  description = "Bedrock model ARNs the AI pod may invoke (InvokeModel ONLY)."
  type        = list(string)
}

variable "eventbridge_bus_arn" {
  description = "ARN of the EventBridge bus the API may publish to (events:PutEvents ONLY)."
  type        = string
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
