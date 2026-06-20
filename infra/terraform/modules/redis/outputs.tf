output "primary_endpoint_address" {
  description = "Primary endpoint address of the Redis replication group."
  value       = aws_elasticache_replication_group.this.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "Reader endpoint address of the Redis replication group."
  value       = aws_elasticache_replication_group.this.reader_endpoint_address
}

output "port" {
  description = "Port Redis listens on."
  value       = var.redis_port
}

output "security_group_id" {
  description = "Security group ID protecting Redis."
  value       = aws_security_group.this.id
}
