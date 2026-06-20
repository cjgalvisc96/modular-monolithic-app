variable "domain_name" {
  description = "Domain name for the hosted zone (e.g. example.com)."
  type        = string
}

variable "create_zone" {
  description = "Whether to create the hosted zone (false to reference an existing one)."
  type        = bool
  default     = true
}

variable "private_zone" {
  description = "Whether the hosted zone is private."
  type        = bool
  default     = false
}

variable "records" {
  description = "DNS records to create in the zone."
  type = list(object({
    name    = string
    type    = string
    ttl     = optional(number, 300)
    records = optional(list(string), [])
    alias = optional(object({
      name                   = string
      zone_id                = string
      evaluate_target_health = optional(bool, false)
    }))
  }))
  default = []
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
