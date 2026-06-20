variable "name" {
  description = "Name prefix for secrets."
  type        = string
  default     = "todo-app"
}

variable "environment" {
  description = "Environment name, used in the secret path (e.g. dev, prod)."
  type        = string
}

variable "db_credentials" {
  description = "Database credentials to store (username/password/host/port/dbname)."
  type = object({
    username = string
    password = string
    host     = optional(string, "")
    port     = optional(number, 5432)
    dbname   = optional(string, "todo")
  })
  sensitive = true
}

variable "cognito_client_secret" {
  description = "Cognito app client secret to store."
  type        = string
  sensitive   = true
  default     = ""
}

variable "recovery_window_in_days" {
  description = "Recovery window before a deleted secret is permanently removed."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
