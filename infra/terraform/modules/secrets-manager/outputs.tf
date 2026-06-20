output "db_secret_arn" {
  description = "ARN of the database credentials secret (scoped in API pod IAM policy)."
  value       = aws_secretsmanager_secret.db.arn
}

output "db_secret_name" {
  description = "Name of the database credentials secret."
  value       = aws_secretsmanager_secret.db.name
}

output "cognito_secret_arn" {
  description = "ARN of the Cognito client secret."
  value       = aws_secretsmanager_secret.cognito.arn
}

output "cognito_secret_name" {
  description = "Name of the Cognito client secret."
  value       = aws_secretsmanager_secret.cognito.name
}
