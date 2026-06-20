variable "bus_name" {
  description = "Name of the custom EventBridge event bus."
  type        = string
  default     = "todo-app-events"
}

variable "rules" {
  description = "Event rules to create on the bus."
  type = list(object({
    name            = string
    description     = optional(string, "")
    event_pattern   = optional(string)
    is_enabled      = optional(bool, true)
    target_arn      = optional(string)
    target_role_arn = optional(string)
  }))
  default = []
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
