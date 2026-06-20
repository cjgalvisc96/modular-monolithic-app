terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  # The OIDC condition keys are derived from the issuer URL (sans scheme).
  oidc_sub = "${var.oidc_provider_url}:sub"
  oidc_aud = "${var.oidc_provider_url}:aud"

  service_account_subjects = {
    api     = "system:serviceaccount:${var.namespace}:${var.api_service_account_name}"
    ai      = "system:serviceaccount:${var.namespace}:${var.ai_service_account_name}"
    db_init = "system:serviceaccount:${var.namespace}:${var.db_init_service_account_name}"
  }
}

# Reusable IRSA trust policy: assume-role-with-web-identity, locked to a single
# Kubernetes service account (sub) and the sts.amazonaws.com audience.
data "aws_iam_policy_document" "irsa_trust" {
  for_each = local.service_account_subjects

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = local.oidc_sub
      values   = [each.value]
    }

    condition {
      test     = "StringEquals"
      variable = local.oidc_aud
      values   = ["sts.amazonaws.com"]
    }
  }
}
