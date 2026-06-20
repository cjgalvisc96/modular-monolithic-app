# DB-init Job IRSA role.
# Least-privilege: connect as the dedicated migrator db user (for DDL/migrations)
# + read its OWN migration secret. Explicitly scoped to a separate db user from
# the runtime API user so it has NO standing access to application data at
# runtime — schema/migration concerns only.

resource "aws_iam_role" "db_init" {
  name                 = "${var.name}-db-init-role"
  assume_role_policy   = data.aws_iam_policy_document.irsa_trust["db_init"].json
  max_session_duration = 3600
  tags                 = merge(var.tags, { Workload = "db-init" })
}

data "aws_iam_policy_document" "db_init" {
  # Connect ONLY as the migrator user (DDL/migrations). This user is distinct
  # from the API runtime user; data-table access is governed at the DB layer.
  statement {
    sid     = "AuroraIamConnectMigrator"
    effect  = "Allow"
    actions = ["rds-db:connect"]
    resources = [
      "arn:aws:rds-db:${var.aws_region}:${var.aws_account_id}:dbuser:${var.aurora_cluster_resource_id}/${var.db_init_iam_username}",
    ]
  }

  # Read ONLY the migration credentials secret.
  statement {
    sid    = "ReadMigrationSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
    ]
    resources = var.db_init_secret_arns
  }
}

resource "aws_iam_role_policy" "db_init" {
  name   = "${var.name}-db-init-policy"
  role   = aws_iam_role.db_init.id
  policy = data.aws_iam_policy_document.db_init.json
}
