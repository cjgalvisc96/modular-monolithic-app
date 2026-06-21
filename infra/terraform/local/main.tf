# floci-targeted local stack: the resources floci can emulate — ECR, SSM, and
# the datastores (Aurora + ElastiCache), which floci backs with postgres/valkey
# containers on the project network. The real cloud stacks live under
# environments/. Excluded from the Trivy gate (deliberately un-hardened).

provider "aws" {
  region     = var.region
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation      = true
  s3_use_path_style           = true

  endpoints {
    ecr         = var.floci_endpoint
    ssm         = var.floci_endpoint
    sts         = var.floci_endpoint
    iam         = var.floci_endpoint
    s3          = var.floci_endpoint
    rds         = var.floci_endpoint
    elasticache = var.floci_endpoint
  }
}

resource "aws_ecr_repository" "app" {
  name                 = var.repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

locals {
  ssm_params = merge([
    for env in var.environments : {
      "/gitops/${env}/todo-app/DB_USER"        = { value = "todo", type = "String" }
      "/gitops/${env}/todo-app/DB_PASSWORD"    = { value = "todo", type = "SecureString" }
      "/gitops/${env}/todo-app/REDIS_PASSWORD" = { value = "redispass", type = "SecureString" }
    }
  ]...)
}

resource "aws_ssm_parameter" "todo_app" {
  for_each  = local.ssm_params
  name      = each.key
  type      = each.value.type
  value     = each.value.value
  overwrite = true
}

# floci reports engine="postgres"/"valkey" and a different cluster shape than the
# provider expects; ignore_changes keeps re-applies idempotent.
resource "aws_rds_cluster" "aurora" {
  cluster_identifier  = "todo-aurora"
  engine              = "aurora-postgresql"
  master_username     = "todo"
  master_password     = var.db_password
  database_name       = "todo"
  skip_final_snapshot = true
  apply_immediately   = true

  lifecycle {
    ignore_changes = [engine, engine_mode]
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "todo-redis"
  description          = "todo local cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_clusters   = 1

  lifecycle {
    ignore_changes = [engine, num_cache_clusters]
  }
}
