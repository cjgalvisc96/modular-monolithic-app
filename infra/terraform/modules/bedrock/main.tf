data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

# Resolve each configured model to its foundation-model data source. This both
# validates the model is available in the region and exposes its canonical ARN.
data "aws_bedrock_foundation_model" "this" {
  for_each = toset(var.model_ids)
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
