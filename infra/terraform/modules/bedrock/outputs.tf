output "model_ids" {
  description = "Bedrock model IDs scoped for the AI bounded context."
  value       = var.model_ids
}

output "model_arns" {
  description = "ARNs of the allowed Bedrock models (consumed by the AI pod IRSA policy)."
  value       = local.model_arns
}

output "resolved_model_arns" {
  description = "Canonical model ARNs resolved from the Bedrock foundation-model data source."
  value       = [for m in data.aws_bedrock_foundation_model.this : m.model_arn]
}
