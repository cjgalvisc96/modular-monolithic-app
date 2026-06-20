output "repository_url" {
  description = "URL of the ECR repository (used as the image registry)."
  value       = aws_ecr_repository.this.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository."
  value       = aws_ecr_repository.this.arn
}

output "repository_name" {
  description = "Name of the ECR repository."
  value       = aws_ecr_repository.this.name
}

output "registry_id" {
  description = "Registry ID (AWS account) the repository belongs to."
  value       = aws_ecr_repository.this.registry_id
}
