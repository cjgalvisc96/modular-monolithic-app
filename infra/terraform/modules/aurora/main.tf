locals {
  # Place instances in the public subnet group only when explicitly requested.
  active_subnet_group = var.publicly_accessible ? aws_db_subnet_group.public[0].name : aws_db_subnet_group.private.name
}

############################################
# DB subnet groups: private (default) + public (optional)
############################################
resource "aws_db_subnet_group" "private" {
  name       = "${var.name}-aurora-private"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, { Name = "${var.name}-aurora-private" })
}

resource "aws_db_subnet_group" "public" {
  count = length(var.public_subnet_ids) > 0 ? 1 : 0

  name       = "${var.name}-aurora-public"
  subnet_ids = var.public_subnet_ids

  tags = merge(var.tags, { Name = "${var.name}-aurora-public" })
}

############################################
# Security group
############################################
resource "aws_security_group" "this" {
  name        = "${var.name}-aurora-sg"
  description = "Security group for ${var.name} Aurora PostgreSQL"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, { Name = "${var.name}-aurora-sg" })
}

resource "aws_vpc_security_group_ingress_rule" "from_allowed" {
  count = length(var.allowed_security_group_ids)

  security_group_id            = aws_security_group.this.id
  referenced_security_group_id = var.allowed_security_group_ids[count.index]
  from_port                    = var.db_port
  to_port                      = var.db_port
  ip_protocol                  = "tcp"
  description                  = "Allow PostgreSQL access from approved workload security groups"
}

resource "aws_vpc_security_group_egress_rule" "vpc" {
  security_group_id = aws_security_group.this.id
  cidr_ipv4         = var.vpc_cidr
  ip_protocol       = "-1"
  description       = "Allow outbound within the VPC only"
}

############################################
# Customer-managed KMS key for storage encryption
############################################
resource "aws_kms_key" "this" {
  description         = "${var.name} Aurora storage encryption"
  enable_key_rotation = true
  tags                = merge(var.tags, { Name = "${var.name}-aurora-kms" })
}

############################################
# Cluster parameter group (enforces TLS, tuned logging)
############################################
resource "aws_rds_cluster_parameter_group" "this" {
  name        = "${var.name}-aurora-pg15"
  family      = "aurora-postgresql15"
  description = "Cluster parameter group for ${var.name} Aurora PostgreSQL"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  tags = var.tags
}

############################################
# Aurora PostgreSQL cluster — IAM database authentication ENABLED
############################################
resource "aws_rds_cluster" "this" {
  cluster_identifier = "${var.name}-aurora"
  engine             = "aurora-postgresql"
  engine_version     = var.engine_version
  database_name      = var.database_name
  master_username    = var.master_username
  master_password    = var.master_password
  port               = var.db_port

  db_subnet_group_name            = local.active_subnet_group
  vpc_security_group_ids          = [aws_security_group.this.id]
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.this.name

  # IAM database authentication — required for IRSA-based rds-db:connect.
  iam_database_authentication_enabled = true

  storage_encrypted         = true
  kms_key_id                = aws_kms_key.this.arn
  backup_retention_period   = var.backup_retention_period
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.name}-aurora-final"

  tags = merge(var.tags, { Name = "${var.name}-aurora" })
}

resource "aws_rds_cluster_instance" "this" {
  count = var.instance_count

  identifier           = "${var.name}-aurora-${count.index}"
  cluster_identifier   = aws_rds_cluster.this.id
  engine               = aws_rds_cluster.this.engine
  engine_version       = aws_rds_cluster.this.engine_version
  instance_class       = var.instance_class
  db_subnet_group_name = local.active_subnet_group
  publicly_accessible  = var.publicly_accessible

  tags = merge(var.tags, { Name = "${var.name}-aurora-${count.index}" })
}
