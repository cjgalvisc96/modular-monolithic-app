variable "name" {
  description = "Name prefix for the Aurora resources."
  type        = string
  default     = "todo-app"
}

variable "vpc_id" {
  description = "VPC ID the cluster lives in."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the primary (private) DB subnet group."
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the public DB subnet group (used only when publicly_accessible = true)."
  type        = list(string)
  default     = []
}

variable "publicly_accessible" {
  description = "Whether instances are placed in the public subnet group and reachable from outside the VPC. Keep false in prod."
  type        = bool
  default     = false
}

variable "engine_version" {
  description = "Aurora PostgreSQL engine version."
  type        = string
  default     = "15.4"
}

variable "database_name" {
  description = "Name of the initial database."
  type        = string
  default     = "todo"
}

variable "master_username" {
  description = "Master username for the cluster."
  type        = string
  default     = "todo_admin"
}

variable "master_password" {
  description = "Master password. Sourced from Secrets Manager — never hardcode."
  type        = string
  sensitive   = true
}

variable "instance_class" {
  description = "Instance class for cluster instances."
  type        = string
  default     = "db.r6g.large"
}

variable "instance_count" {
  description = "Number of cluster instances (1 writer + N-1 readers)."
  type        = number
  default     = 2
}

variable "allowed_security_group_ids" {
  description = "Security group IDs allowed to connect to the database port."
  type        = list(string)
  default     = []
}

variable "db_port" {
  description = "Port the database listens on."
  type        = number
  default     = 5432
}

variable "backup_retention_period" {
  description = "Number of days to retain automated backups."
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "Enable deletion protection on the cluster."
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Skip the final snapshot on deletion (true for dev convenience)."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
