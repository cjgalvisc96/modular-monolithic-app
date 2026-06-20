variable "name" {
  description = "Name prefix for the distribution."
  type        = string
  default     = "todo-app"
}

variable "s3_bucket_id" {
  description = "ID (name) of the S3 bucket origin."
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket origin (used in the OAC bucket policy)."
  type        = string
}

variable "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket origin."
  type        = string
}

variable "aliases" {
  description = "CNAME aliases for the distribution."
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ARN of an ACM certificate in us-east-1 for the aliases. When empty, the default CloudFront certificate is used."
  type        = string
  default     = ""
}

variable "price_class" {
  description = "CloudFront price class."
  type        = string
  default     = "PriceClass_100"
}

variable "default_root_object" {
  description = "Default root object served at the distribution root."
  type        = string
  default     = "index.html"
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}
