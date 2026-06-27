variable "model_ids" {
  description = "Bedrock foundation model IDs the AI bounded context is allowed to invoke."
  type        = list(string)
  default = [
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
  ]
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}

variable "enable_model_validation" {
  description = "Look up each model via the Bedrock foundation-model data source (validates availability). Set false on emulators without the Bedrock management API (e.g. floci)."
  type        = bool
  default     = true
}
