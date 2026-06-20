# API pod IRSA role.
# Least-privilege: Aurora IAM auth (rds-db:connect to ONE db user) + read of ITS
# OWN Secrets Manager secrets only. No data-plane AWS access beyond that.

resource "aws_iam_role" "api" {
  name                 = "${var.name}-api-pod-role"
  assume_role_policy   = data.aws_iam_policy_document.irsa_trust["api"].json
  max_session_duration = 3600
  tags                 = merge(var.tags, { Workload = "api" })
}

data "aws_iam_policy_document" "api" {
  # Aurora IAM database authentication for the specific db user only.
  statement {
    sid     = "AuroraIamConnect"
    effect  = "Allow"
    actions = ["rds-db:connect"]
    resources = [
      "arn:aws:rds-db:${var.aws_region}:${var.aws_account_id}:dbuser:${var.aurora_cluster_resource_id}/${var.db_iam_username}",
    ]
  }

  # Read ONLY the API's own secrets (DB creds + Cognito client secret).
  statement {
    sid    = "ReadOwnSecrets"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = var.api_secret_arns
  }
}

resource "aws_iam_role_policy" "api" {
  name   = "${var.name}-api-pod-policy"
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.api.json
}
