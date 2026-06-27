output "cluster_name" {
  description = "Name of the EKS cluster."
  value       = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  description = "Endpoint for the EKS Kubernetes API server."
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64-encoded certificate authority data for the cluster."
  value       = aws_eks_cluster.this.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS control plane."
  value       = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

output "oidc_provider_arn" {
  description = "ARN of the IAM OIDC provider (consumed by IRSA roles)."
  value       = try(one(aws_iam_openid_connect_provider.oidc[*].arn), "")
}

output "oidc_provider_url" {
  description = "URL of the cluster OIDC issuer (without the https:// scheme), used in IRSA trust conditions."
  value       = try(replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", ""), "")
}

output "node_role_arn" {
  description = "ARN of the IAM role used by the managed node group."
  value       = aws_iam_role.node.arn
}
