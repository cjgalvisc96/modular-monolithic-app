variable "name" {
  description = "Name prefix for Cognito resources."
  type        = string
  default     = "todo-app"
}

variable "user_pool_name" {
  description = "Name of the Cognito User Pool."
  type        = string
  default     = "todo-app-users"
}

variable "domain_prefix" {
  description = "Prefix for the Cognito-hosted user pool domain (must be globally unique)."
  type        = string
}

variable "app_client_name" {
  description = "Name of the app client."
  type        = string
  default     = "todo-app-client"
}

variable "callback_urls" {
  description = "Allowed OAuth callback URLs for the app client."
  type        = list(string)
  default     = ["https://localhost/callback"]
}

variable "logout_urls" {
  description = "Allowed OAuth logout URLs for the app client."
  type        = list(string)
  default     = ["https://localhost/logout"]
}

variable "generate_client_secret" {
  description = "Whether to generate a client secret (stored in Secrets Manager)."
  type        = bool
  default     = true
}

variable "lambda_runtime" {
  description = "Runtime for the pre-token-generation Lambda."
  type        = string
  default     = "python3.12"
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
