resource "aws_elasticache_subnet_group" "this" {
  name       = "${var.name}-redis-subnets"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, { Name = "${var.name}-redis-subnets" })
}

resource "aws_security_group" "this" {
  name        = "${var.name}-redis-sg"
  description = "Security group for ${var.name} ElastiCache Redis"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, { Name = "${var.name}-redis-sg" })
}

resource "aws_vpc_security_group_ingress_rule" "from_allowed" {
  count = length(var.allowed_security_group_ids)

  security_group_id            = aws_security_group.this.id
  referenced_security_group_id = var.allowed_security_group_ids[count.index]
  from_port                    = var.redis_port
  to_port                      = var.redis_port
  ip_protocol                  = "tcp"
  description                  = "Allow Redis access from approved workload security groups"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.this.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound"
}

resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.name}-redis"
  description          = "${var.name} Redis replication group"

  engine         = "redis"
  engine_version = var.engine_version
  node_type      = var.node_type
  port           = var.redis_port

  num_cache_clusters         = var.num_cache_clusters
  automatic_failover_enabled = var.automatic_failover_enabled
  multi_az_enabled           = var.multi_az_enabled

  subnet_group_name  = aws_elasticache_subnet_group.this.name
  security_group_ids = [aws_security_group.this.id]

  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  transit_encryption_enabled = var.transit_encryption_enabled

  tags = merge(var.tags, { Name = "${var.name}-redis" })
}
