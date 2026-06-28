terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

locals {
  name          = "${var.project}-${var.environment}"
  k8s_namespace = "todo-app"

  tags = {
    Owner       = var.owner
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }

  # floci disables aurora/redis/cognito (LocalStack can't apply them); one(...) is null when count is 0.
  db_host                    = var.floci ? "postgres" : one(module.aurora[*].endpoint)
  db_port                    = var.floci ? 5432 : one(module.aurora[*].port)
  db_name                    = var.floci ? "todo" : one(module.aurora[*].database_name)
  cognito_client_secret      = var.floci ? "floci-stub-cognito-secret" : one(module.cognito[*].app_client_secret)
  aurora_cluster_resource_id = var.floci ? "*" : one(module.aurora[*].cluster_resource_id)
}

module "vpc" {
  source = "../../modules/vpc"
  # floci: platform (local-gitops) owns the k3s workload cluster, so VPC/EKS are parity-only here.
  count = var.floci ? 0 : 1

  name                 = local.name
  cidr_block           = "10.20.0.0/16"
  azs                  = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  public_subnet_cidrs  = ["10.20.0.0/20", "10.20.16.0/20", "10.20.32.0/20"]
  private_subnet_cidrs = ["10.20.128.0/20", "10.20.144.0/20", "10.20.160.0/20"]
  single_nat_gateway   = false
  enable_nat           = !var.floci # floci can't ReplaceRoute; k3s needs no NAT
  eks_cluster_name     = local.name
  tags                 = local.tags
}

module "eks" {
  source = "../../modules/eks"
  count  = var.floci ? 0 : 1 # floci: k3s container owned by the platform (see vpc)

  cluster_name       = local.name
  kubernetes_version = "1.30"
  enable_irsa        = !var.floci
  vpc_id             = one(module.vpc[*].vpc_id)
  private_subnet_ids = one(module.vpc[*].private_subnet_ids)
  public_subnet_ids  = one(module.vpc[*].public_subnet_ids)

  endpoint_public_access = false
  node_instance_types    = ["m6i.xlarge"]
  node_desired_size      = 3
  node_min_size          = 3
  node_max_size          = 8
  tags                   = local.tags
}

module "ecr" {
  source = "../../modules/ecr"

  # Env-scoped name so it doesn't collide with the dev `todo-app` repo on the shared floci account.
  repository_name      = local.name
  image_tag_mutability = "IMMUTABLE"
  max_tagged_images    = 50
  tags                 = local.tags
}

module "aurora" {
  source = "../../modules/aurora"
  count  = var.floci ? 0 : 1

  name                       = local.name
  vpc_id                     = one(module.vpc[*].vpc_id)
  vpc_cidr                   = one(module.vpc[*].vpc_cidr_block)
  private_subnet_ids         = one(module.vpc[*].private_subnet_ids)
  publicly_accessible        = false
  master_password            = var.db_master_password
  instance_class             = "db.r6g.large"
  instance_count             = 2
  allowed_security_group_ids = [one(module.eks[*].cluster_security_group_id)]
  backup_retention_period    = 30
  deletion_protection        = true
  skip_final_snapshot        = false
  tags                       = local.tags
}

module "redis" {
  source = "../../modules/redis"
  count  = var.floci ? 0 : 1

  name                       = local.name
  vpc_id                     = one(module.vpc[*].vpc_id)
  vpc_cidr                   = one(module.vpc[*].vpc_cidr_block)
  private_subnet_ids         = one(module.vpc[*].private_subnet_ids)
  allowed_security_group_ids = [one(module.eks[*].cluster_security_group_id)]
  node_type                  = "cache.r6g.large"
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled           = true
  tags                       = local.tags
}

module "cognito" {
  source = "../../modules/cognito"
  count  = var.floci ? 0 : 1

  name           = local.name
  user_pool_name = "${local.name}-users"
  domain_prefix  = var.cognito_domain_prefix
  callback_urls  = ["https://${var.domain_name}/callback"]
  logout_urls    = ["https://${var.domain_name}/logout"]
  tags           = local.tags
}

module "secrets" {
  source = "../../modules/secrets-manager"

  name        = var.project
  environment = var.environment
  db_credentials = {
    username = "todo_admin"
    password = var.db_master_password
    host     = local.db_host
    port     = local.db_port
    dbname   = local.db_name
  }
  cognito_client_secret   = local.cognito_client_secret
  recovery_window_in_days = 30
  tags                    = local.tags
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  bus_name = "${local.name}-events"
  tags     = local.tags
}

module "sqs_sns" {
  source = "../../modules/sqs-sns"

  name       = local.name
  topic_name = "${local.name}-tasks"
  queue_name = "${local.name}-tasks"
  tags       = local.tags
}

module "bedrock" {
  source = "../../modules/bedrock"

  model_ids               = var.bedrock_model_ids
  enable_model_validation = var.bedrock_validate_models
  tags                    = local.tags
}

module "s3_assets" {
  source = "../../modules/s3"

  bucket_name   = "${local.name}-assets-${data.aws_caller_identity.current.account_id}"
  force_destroy = false
  tags          = local.tags
}

module "cdn" {
  source = "../../modules/cdn"
  count  = var.floci ? 0 : 1

  name                           = local.name
  s3_bucket_id                   = module.s3_assets.bucket_id
  s3_bucket_arn                  = module.s3_assets.bucket_arn
  s3_bucket_regional_domain_name = module.s3_assets.bucket_regional_domain_name
  price_class                    = "PriceClass_All"
  tags                           = local.tags
}

module "route53" {
  source = "../../modules/route53"
  count  = var.floci ? 0 : 1

  domain_name = var.domain_name
  create_zone = true
  records = [
    {
      name = var.domain_name
      type = "A"
      alias = {
        name                   = one(module.cdn[*].domain_name)
        zone_id                = one(module.cdn[*].hosted_zone_id)
        evaluate_target_health = false
      }
    },
  ]
  tags = local.tags
}

module "iam" {
  source = "../../modules/iam"
  count  = var.floci ? 0 : 1

  name              = local.name
  oidc_provider_arn = one(module.eks[*].oidc_provider_arn)
  oidc_provider_url = one(module.eks[*].oidc_provider_url)
  namespace         = local.k8s_namespace

  aurora_cluster_resource_id = local.aurora_cluster_resource_id
  aws_region                 = var.aws_region
  aws_account_id             = data.aws_caller_identity.current.account_id

  api_secret_arns     = [module.secrets.db_secret_arn, module.secrets.cognito_secret_arn]
  db_init_secret_arns = [module.secrets.db_secret_arn]
  bedrock_model_arns  = module.bedrock.model_arns
  eventbridge_bus_arn = module.eventbridge.bus_arn

  tags = local.tags
}
