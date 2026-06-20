terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

############################################
# Pre-token-generation Lambda (defined in submodule)
############################################
module "pre_token_lambda" {
  source = "./pre_token_lambda"

  function_name = "${var.name}-pre-token-generation"
  user_pool_arn = aws_cognito_user_pool.this.arn
  runtime       = var.lambda_runtime
  tags          = var.tags
}

############################################
# Single multi-tenant User Pool
############################################
resource "aws_cognito_user_pool" "this" {
  name = var.user_pool_name

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Custom attribute carrying the tenant identifier for multi-tenancy/RLS.
  schema {
    name                     = "tenant_id"
    attribute_data_type      = "String"
    mutable                  = true
    developer_only_attribute = false
    required                 = false

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Wire the pre-token-generation trigger that injects tenant_id + group claims.
  lambda_config {
    pre_token_generation = module.pre_token_lambda.function_arn
  }

  tags = merge(var.tags, { Name = var.user_pool_name })
}

############################################
# Hosted UI domain
############################################
resource "aws_cognito_user_pool_domain" "this" {
  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}

############################################
# App client
############################################
resource "aws_cognito_user_pool_client" "this" {
  name         = var.app_client_name
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = var.generate_client_secret

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  callback_urls                        = var.callback_urls
  logout_urls                          = var.logout_urls
  supported_identity_providers         = ["COGNITO"]

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  # Allow the app client to read/write the tenant_id custom attribute.
  read_attributes  = ["email", "custom:tenant_id"]
  write_attributes = ["email", "custom:tenant_id"]

  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}
