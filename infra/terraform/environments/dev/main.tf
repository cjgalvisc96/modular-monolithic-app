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

# us-east-1 provider for CloudFront ACM certs (referenced by the CDN when used).
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

locals {
  name          = "${var.project}-${var.environment}"
  k8s_namespace = "dev-app"

  tags = {
    Owner       = var.owner
    Environment = var.environment
    Project     = var.project
    ManagedBy   = "terraform"
  }
}

############################################
# Network
############################################
module "vpc" {
  source = "../../modules/vpc"

  name                 = local.name
  cidr_block           = "10.10.0.0/16"
  azs                  = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnet_cidrs  = ["10.10.0.0/20", "10.10.16.0/20"]
  private_subnet_cidrs = ["10.10.128.0/20", "10.10.144.0/20"]
  single_nat_gateway   = true # dev: one NAT to save cost
  eks_cluster_name     = local.name
  tags                 = local.tags
}

############################################
# EKS (OIDC enabled for IRSA)
############################################
module "eks" {
  source = "../../modules/eks"

  cluster_name       = local.name
  kubernetes_version = "1.30"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids

  node_instance_types = ["t3.large"]
  node_desired_size   = 2
  node_min_size       = 2
  node_max_size       = 3
  tags                = local.tags
}

############################################
# Container registry
############################################
module "ecr" {
  source = "../../modules/ecr"

  repository_name      = var.project
  image_tag_mutability = "MUTABLE" # dev: allow tag reuse
  tags                 = local.tags
}

############################################
# Data stores
############################################
module "aurora" {
  source = "../../modules/aurora"

  name                       = local.name
  vpc_id                     = module.vpc.vpc_id
  private_subnet_ids         = module.vpc.private_subnet_ids
  public_subnet_ids          = module.vpc.public_subnet_ids
  master_password            = var.db_master_password
  instance_class             = "db.t4g.medium"
  instance_count             = 1
  allowed_security_group_ids = [module.eks.cluster_security_group_id]
  deletion_protection        = false
  skip_final_snapshot        = true
  tags                       = local.tags
}

module "redis" {
  source = "../../modules/redis"

  name                       = local.name
  vpc_id                     = module.vpc.vpc_id
  private_subnet_ids         = module.vpc.private_subnet_ids
  allowed_security_group_ids = [module.eks.cluster_security_group_id]
  node_type                  = "cache.t4g.small"
  num_cache_clusters         = 1
  automatic_failover_enabled = false
  multi_az_enabled           = false
  tags                       = local.tags
}

############################################
# Identity
############################################
module "cognito" {
  source = "../../modules/cognito"

  name           = local.name
  user_pool_name = "${local.name}-users"
  domain_prefix  = var.cognito_domain_prefix
  callback_urls  = ["https://${var.domain_name}/callback"]
  logout_urls    = ["https://${var.domain_name}/logout"]
  tags           = local.tags
}

############################################
# Secrets (DB creds + Cognito client secret)
############################################
module "secrets" {
  source = "../../modules/secrets-manager"

  name        = var.project
  environment = var.environment
  db_credentials = {
    username = "todo_admin"
    password = var.db_master_password
    host     = module.aurora.endpoint
    port     = module.aurora.port
    dbname   = module.aurora.database_name
  }
  cognito_client_secret = module.cognito.app_client_secret
  tags                  = local.tags
}

############################################
# Async / messaging
############################################
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

############################################
# Bedrock scoping
############################################
module "bedrock" {
  source = "../../modules/bedrock"

  model_ids = var.bedrock_model_ids
  tags      = local.tags
}

############################################
# Static assets + CDN
############################################
module "s3_assets" {
  source = "../../modules/s3"

  bucket_name   = "${local.name}-assets-${data.aws_caller_identity.current.account_id}"
  force_destroy = true # dev
  tags          = local.tags
}

module "cdn" {
  source = "../../modules/cdn"

  name                           = local.name
  s3_bucket_id                   = module.s3_assets.bucket_id
  s3_bucket_arn                  = module.s3_assets.bucket_arn
  s3_bucket_regional_domain_name = module.s3_assets.bucket_regional_domain_name
  tags                           = local.tags
}

############################################
# DNS
############################################
module "route53" {
  source = "../../modules/route53"

  domain_name = var.domain_name
  create_zone = true
  records = [
    {
      name = var.domain_name
      type = "A"
      alias = {
        name                   = module.cdn.domain_name
        zone_id                = module.cdn.hosted_zone_id
        evaluate_target_health = false
      }
    },
  ]
  tags = local.tags
}

############################################
# Least-privilege IRSA roles
############################################
module "iam" {
  source = "../../modules/iam"

  name              = local.name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  namespace         = local.k8s_namespace

  aurora_cluster_resource_id = module.aurora.cluster_resource_id
  aws_region                 = var.aws_region
  aws_account_id             = data.aws_caller_identity.current.account_id

  api_secret_arns     = [module.secrets.db_secret_arn, module.secrets.cognito_secret_arn]
  db_init_secret_arns = [module.secrets.db_secret_arn]
  bedrock_model_arns  = module.bedrock.model_arns
  eventbridge_bus_arn = module.eventbridge.bus_arn

  tags = local.tags
}
