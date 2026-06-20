output "bus_name" {
  description = "Name of the event bus."
  value       = aws_cloudwatch_event_bus.this.name
}

output "bus_arn" {
  description = "ARN of the event bus (scoped in the EventBridge publish-only IAM policy)."
  value       = aws_cloudwatch_event_bus.this.arn
}

output "rule_arns" {
  description = "ARNs of the event rules created."
  value       = { for k, r in aws_cloudwatch_event_rule.this : k => r.arn }
}
