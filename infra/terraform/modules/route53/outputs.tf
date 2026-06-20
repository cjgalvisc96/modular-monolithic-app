output "zone_id" {
  description = "Hosted zone ID."
  value       = local.zone_id
}

output "name_servers" {
  description = "Name servers for the hosted zone (only set when the zone is created here)."
  value       = var.create_zone ? aws_route53_zone.this[0].name_servers : []
}

output "record_fqdns" {
  description = "FQDNs of the records created."
  value       = [for r in aws_route53_record.this : r.fqdn]
}
