resource "aws_route53_zone" "this" {
  count = var.create_zone ? 1 : 0

  name = var.domain_name

  dynamic "vpc" {
    for_each = var.private_zone ? [1] : []
    content {
      vpc_id = vpc.value
    }
  }

  tags = merge(var.tags, { Name = var.domain_name })
}

data "aws_route53_zone" "existing" {
  count = var.create_zone ? 0 : 1

  name         = var.domain_name
  private_zone = var.private_zone
}

locals {
  zone_id = var.create_zone ? aws_route53_zone.this[0].zone_id : data.aws_route53_zone.existing[0].zone_id
}

resource "aws_route53_record" "this" {
  for_each = { for r in var.records : "${r.name}-${r.type}" => r }

  zone_id = local.zone_id
  name    = each.value.name
  type    = each.value.type

  # Standard records carry a TTL + record set; alias records do not.
  ttl     = each.value.alias == null ? each.value.ttl : null
  records = each.value.alias == null ? each.value.records : null

  dynamic "alias" {
    for_each = each.value.alias == null ? [] : [each.value.alias]
    content {
      name                   = alias.value.name
      zone_id                = alias.value.zone_id
      evaluate_target_health = alias.value.evaluate_target_health
    }
  }
}
