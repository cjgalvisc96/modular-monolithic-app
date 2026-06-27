data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# Resolve each configured model to its foundation-model data source. This both
# validates the model is available in the region and exposes its canonical ARN.
# Disable on emulators that lack the Bedrock *management* API (e.g. floci) — the
# IAM-consumed `model_arns` are computed locally below and don't need it.
data "aws_bedrock_foundation_model" "this" {
  for_each = var.enable_model_validation ? toset(var.model_ids) : toset([])
  model_id = each.value
}

locals {
  region     = data.aws_region.current.name
  account_id = data.aws_caller_identity.current.account_id
  partition  = data.aws_partition.current.partition

  # Foundation-model ARNs are account-agnostic (aws:bedrock:<region>::foundation-model/<id>).
  model_arns = [
    for id in var.model_ids :
    "arn:${local.partition}:bedrock:${local.region}::foundation-model/${id}"
  ]
}
