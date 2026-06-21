output "repository_url" {
  description = "ECR repository URL (push target) on floci."
  value       = aws_ecr_repository.app.repository_url
}

output "ssm_parameter_names" {
  description = "SSM parameter names seeded for the app / GitOps ExternalSecret."
  value       = sort(keys(local.ssm_params))
}

output "aurora_cluster_endpoint" {
  description = "Aurora (RDS) cluster endpoint reported by floci."
  value       = aws_rds_cluster.aurora.endpoint
}

output "elasticache_id" {
  description = "ElastiCache (Redis) replication group id."
  value       = aws_elasticache_replication_group.redis.replication_group_id
}
