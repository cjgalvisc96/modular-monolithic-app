variable "name" {
  description = "Name prefix for the Redis resources."
  type        = string
  default     = "todo-app"
}

variable "vpc_cidr" {
  description = "VPC CIDR the Redis security group may send egress to (no public egress)."
  type        = string
  default     = "10.0.0.0/16"
}

variable "vpc_id" {
  description = "VPC ID the Redis cluster lives in."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the cache subnet group."
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs allowed to reach Redis on the Redis port."
  type        = list(string)
  default     = []
}

variable "engine_version" {
  description = "Redis engine version."
  type        = string
  default     = "7.1"
}

variable "node_type" {
  description = "ElastiCache node instance type."
  type        = string
  default     = "cache.t4g.small"
}

variable "num_cache_clusters" {
  description = "Number of nodes in the replication group (1 = no replica)."
  type        = number
  default     = 2
}

variable "automatic_failover_enabled" {
  description = "Enable automatic failover (requires >= 2 nodes across AZs)."
  type        = bool
  default     = true
}

variable "multi_az_enabled" {
  description = "Enable Multi-AZ for the replication group."
  type        = bool
  default     = true
}

variable "at_rest_encryption_enabled" {
  description = "Enable encryption at rest."
  type        = bool
  default     = true
}

variable "transit_encryption_enabled" {
  description = "Enable encryption in transit (TLS)."
  type        = bool
  default     = true
}

variable "redis_port" {
  description = "Port Redis listens on."
  type        = number
  default     = 6379
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
