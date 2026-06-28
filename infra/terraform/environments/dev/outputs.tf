output "vpc_id" {
  description = "VPC ID (null on floci — the platform owns the k3s workload cluster)."
  value       = one(module.vpc[*].vpc_id)
}

output "eks_cluster_name" {
  description = "EKS cluster name (null on floci)."
  value       = one(module.eks[*].cluster_name)
}

output "eks_oidc_provider_arn" {
  description = "EKS OIDC provider ARN (IRSA; null on floci)."
  value       = one(module.eks[*].oidc_provider_arn)
}

output "ecr_repository_url" {
  description = "ECR repository URL."
  value       = module.ecr.repository_url
}

output "aurora_endpoint" {
  description = "Aurora writer endpoint."
  value       = one(module.aurora[*].endpoint)
}

output "redis_endpoint" {
  description = "Redis primary endpoint."
  value       = one(module.redis[*].primary_endpoint_address)
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID."
  value       = one(module.cognito[*].user_pool_id)
}

output "cognito_app_client_id" {
  description = "Cognito app client ID."
  value       = one(module.cognito[*].app_client_id)
}

output "cdn_domain_name" {
  description = "CloudFront distribution domain name."
  value       = one(module.cdn[*].domain_name)
}

output "irsa_api_pod_role_arn" {
  description = "IRSA role ARN for the API pod."
  value       = one(module.iam[*].api_pod_role_arn)
}

output "irsa_ai_pod_role_arn" {
  description = "IRSA role ARN for the AI pod."
  value       = one(module.iam[*].ai_pod_role_arn)
}

output "irsa_db_init_role_arn" {
  description = "IRSA role ARN for the DB-init Job."
  value       = one(module.iam[*].db_init_job_role_arn)
}

output "irsa_eventbridge_role_arn" {
  description = "IRSA role ARN for the EventBridge publisher."
  value       = one(module.iam[*].eventbridge_role_arn)
}
