locals {
  prefix = "${var.name}/${var.environment}"
}

############################################
# Database credentials secret
############################################
resource "aws_secretsmanager_secret" "db" {
  name                    = "${local.prefix}/db-credentials"
  description             = "Aurora PostgreSQL credentials for ${var.name} (${var.environment})"
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(var.tags, { Name = "${local.prefix}/db-credentials" })
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_credentials.username
    password = var.db_credentials.password
    host     = var.db_credentials.host
    port     = var.db_credentials.port
    dbname   = var.db_credentials.dbname
  })
}

############################################
# Cognito client secret
############################################
resource "aws_secretsmanager_secret" "cognito" {
  name                    = "${local.prefix}/cognito-client-secret"
  description             = "Cognito app client secret for ${var.name} (${var.environment})"
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(var.tags, { Name = "${local.prefix}/cognito-client-secret" })
}

resource "aws_secretsmanager_secret_version" "cognito" {
  secret_id     = aws_secretsmanager_secret.cognito.id
  secret_string = var.cognito_client_secret
}
