# The four IRSA role ARNs consumed by the Helm chart's service accounts
# (eks.amazonaws.com/role-arn annotation).

output "api_pod_role_arn" {
  description = "ARN of the API pod IRSA role (Aurora IAM auth + own secrets)."
  value       = aws_iam_role.api.arn
}

output "ai_pod_role_arn" {
  description = "ARN of the AI pod IRSA role (bedrock:InvokeModel on specific models only)."
  value       = aws_iam_role.ai.arn
}

output "db_init_job_role_arn" {
  description = "ARN of the DB-init Job IRSA role (migrations + migration secret only)."
  value       = aws_iam_role.db_init.arn
}

output "eventbridge_role_arn" {
  description = "ARN of the EventBridge publisher IRSA role (events:PutEvents to the bus only)."
  value       = aws_iam_role.eventbridge.arn
}
