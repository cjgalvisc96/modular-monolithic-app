variable "name" {
  description = "Name prefix for the security-baseline resources."
  type        = string
}

variable "log_retention_days" {
  description = "Retention for the CloudTrail object lifecycle in the audit bucket."
  type        = number
  default     = 365
}

variable "trail_bucket_force_destroy" {
  description = "Allow deleting the audit-log bucket while non-empty. Keep false in prod."
  type        = bool
  default     = false
}

variable "enable_security_hub_standards" {
  description = "Subscribe Security Hub to the AWS Foundational Security Best Practices standard."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default     = {}
}
