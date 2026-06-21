output "repository_url" {
  description = "ECR repository URL (push target) on floci."
  value       = aws_ecr_repository.app.repository_url
}

output "ssm_parameter_names" {
  description = "SSM parameter names seeded for the app / GitOps ExternalSecret."
  value       = sort(keys(local.ssm_params))
}
