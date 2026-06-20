variable "repository_name" {
  description = "Name of the ECR repository."
  type        = string
  default     = "todo-app"
}

variable "image_tag_mutability" {
  description = "Tag mutability setting (MUTABLE or IMMUTABLE)."
  type        = string
  default     = "IMMUTABLE"
}

variable "scan_on_push" {
  description = "Enable image vulnerability scanning on push."
  type        = bool
  default     = true
}

variable "max_tagged_images" {
  description = "Number of most-recent tagged images to retain."
  type        = number
  default     = 20
}

variable "untagged_expiry_days" {
  description = "Number of days after which untagged images expire."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
