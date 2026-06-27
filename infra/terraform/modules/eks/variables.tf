variable "cluster_name" {
  description = "Name of the EKS cluster."
  type        = string
  default     = "todo-app"
}

variable "kubernetes_version" {
  description = "Kubernetes control plane version."
  type        = string
  default     = "1.30"
}

variable "vpc_id" {
  description = "VPC ID the cluster is deployed into."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the control plane ENIs and worker nodes."
  type        = list(string)
}

variable "public_subnet_ids" {
  description = "Public subnet IDs (used when public endpoint access is required)."
  type        = list(string)
  default     = []
}

variable "endpoint_public_access" {
  description = "Whether the EKS API server endpoint is publicly accessible. Private by default."
  type        = bool
  default     = false
}

variable "endpoint_private_access" {
  description = "Whether the EKS API server endpoint is privately accessible from within the VPC."
  type        = bool
  default     = true
}

variable "public_access_cidrs" {
  description = "CIDRs allowed to reach the public API endpoint (only used when endpoint_public_access=true). Must not be 0.0.0.0/0."
  type        = list(string)
  default     = ["10.0.0.0/8"]
}

variable "node_instance_types" {
  description = "Instance types for the managed node group."
  type        = list(string)
  default     = ["t3.large"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of worker nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum number of worker nodes."
  type        = number
  default     = 4
}

variable "node_capacity_type" {
  description = "Capacity type for the node group (ON_DEMAND or SPOT)."
  type        = string
  default     = "ON_DEMAND"
}

variable "aws_auth_roles" {
  description = "Additional IAM roles to map into the aws-auth ConfigMap (rolearn/username/groups)."
  type = list(object({
    rolearn  = string
    username = string
    groups   = list(string)
  }))
  default = []
}

variable "tags" {
  description = "Common tags applied to all resources."
  type        = map(string)
  default     = {}
}

variable "enable_irsa" {
  description = "Provision the OIDC provider + aws-auth ConfigMap for IRSA. Set false on floci (its EKS has no OIDC issuer and k3s ignores aws-auth)."
  type        = bool
  default     = true
}
