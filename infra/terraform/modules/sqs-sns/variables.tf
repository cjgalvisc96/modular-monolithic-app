variable "name" {
  description = "Name prefix for the queue/topic."
  type        = string
  default     = "todo-app"
}

variable "topic_name" {
  description = "Name of the SNS topic."
  type        = string
  default     = "todo-app-tasks"
}

variable "queue_name" {
  description = "Name of the SQS queue."
  type        = string
  default     = "todo-app-tasks"
}

variable "visibility_timeout_seconds" {
  description = "SQS visibility timeout in seconds."
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "SQS message retention period in seconds."
  type        = number
  default     = 345600
}

variable "max_receive_count" {
  description = "Number of receives before a message is moved to the dead-letter queue."
  type        = number
  default     = 5
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
