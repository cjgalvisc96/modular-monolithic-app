output "audit_bucket" {
  description = "Name of the audit-log S3 bucket (CloudTrail)."
  value       = aws_s3_bucket.audit.id
}

output "cloudtrail_arn" {
  description = "ARN of the multi-region CloudTrail."
  value       = aws_cloudtrail.main.arn
}

output "guardduty_detector_id" {
  description = "GuardDuty detector ID."
  value       = aws_guardduty_detector.main.id
}

output "access_analyzer_arn" {
  description = "IAM Access Analyzer ARN."
  value       = aws_accessanalyzer_analyzer.main.arn
}
