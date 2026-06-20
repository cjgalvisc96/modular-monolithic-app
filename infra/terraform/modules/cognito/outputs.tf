output "user_pool_id" {
  description = "ID of the Cognito User Pool."
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool."
  value       = aws_cognito_user_pool.this.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool (issuer for JWT validation)."
  value       = aws_cognito_user_pool.this.endpoint
}

output "app_client_id" {
  description = "ID of the app client."
  value       = aws_cognito_user_pool_client.this.id
}

output "app_client_secret" {
  description = "Generated app client secret (store in Secrets Manager)."
  value       = aws_cognito_user_pool_client.this.client_secret
  sensitive   = true
}

output "domain" {
  description = "Hosted UI domain prefix."
  value       = aws_cognito_user_pool_domain.this.domain
}

output "pre_token_lambda_arn" {
  description = "ARN of the pre-token-generation Lambda."
  value       = module.pre_token_lambda.function_arn
}

output "group_names" {
  description = "Names of the RBAC groups."
  value       = [aws_cognito_user_group.admin.name, aws_cognito_user_group.member.name]
}
