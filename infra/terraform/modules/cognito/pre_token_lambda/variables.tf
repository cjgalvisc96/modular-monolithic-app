variable "function_name" {
  description = "Name of the pre-token-generation Lambda function."
  type        = string
  default     = "todo-app-pre-token-generation"
}

variable "user_pool_arn" {
  description = "ARN of the Cognito User Pool that invokes this Lambda (used to scope the invoke permission)."
  type        = string
}

variable "runtime" {
  description = "Lambda runtime."
  type        = string
  default     = "python3.12"
}

variable "claim_prefix" {
  description = "Optional prefix applied to injected claim names."
  type        = string
  default     = ""
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the Lambda."
  type        = number
  default     = 14
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
