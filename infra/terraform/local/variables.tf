variable "floci_endpoint" {
  description = "floci (local AWS emulator) endpoint as seen from the host running Terraform."
  type        = string
  default     = "http://localhost:4576"
}

variable "region" {
  description = "AWS region to emulate."
  type        = string
  default     = "us-east-1"
}

variable "repository_name" {
  description = "ECR repository name for the app image."
  type        = string
  default     = "todo-app"
}

variable "environments" {
  description = "Logical environments whose SSM parameters are seeded (mirrors local-gitops)."
  type        = list(string)
  default     = ["dev", "prod"]
}
