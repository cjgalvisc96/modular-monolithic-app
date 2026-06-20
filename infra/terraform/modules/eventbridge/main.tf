resource "aws_cloudwatch_event_bus" "this" {
  name = var.bus_name
  tags = merge(var.tags, { Name = var.bus_name })
}

resource "aws_cloudwatch_event_rule" "this" {
  for_each = { for r in var.rules : r.name => r }

  name           = each.value.name
  description    = each.value.description
  event_bus_name = aws_cloudwatch_event_bus.this.name
  event_pattern  = each.value.event_pattern
  state          = each.value.is_enabled ? "ENABLED" : "DISABLED"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "this" {
  for_each = { for r in var.rules : r.name => r if r.target_arn != null }

  rule           = aws_cloudwatch_event_rule.this[each.key].name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  arn            = each.value.target_arn
  role_arn       = each.value.target_role_arn
}
