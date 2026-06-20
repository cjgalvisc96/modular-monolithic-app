output "cluster_identifier" {
  description = "Aurora cluster identifier."
  value       = aws_rds_cluster.this.cluster_identifier
}

output "cluster_resource_id" {
  description = "Cluster resource ID — used to build rds-db:connect ARNs for IAM auth."
  value       = aws_rds_cluster.this.cluster_resource_id
}

output "endpoint" {
  description = "Writer endpoint for the Aurora cluster."
  value       = aws_rds_cluster.this.endpoint
}

output "reader_endpoint" {
  description = "Reader endpoint for the Aurora cluster."
  value       = aws_rds_cluster.this.reader_endpoint
}

output "port" {
  description = "Port the database listens on."
  value       = aws_rds_cluster.this.port
}

output "database_name" {
  description = "Name of the initial database."
  value       = aws_rds_cluster.this.database_name
}

output "security_group_id" {
  description = "Security group ID protecting the database."
  value       = aws_security_group.this.id
}
