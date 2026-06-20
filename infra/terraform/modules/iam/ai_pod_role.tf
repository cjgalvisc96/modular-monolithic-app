# AI pod IRSA role.
# Least-privilege: bedrock:InvokeModel (+ streaming variant) on SPECIFIC model
# ARNs only. No S3, no broad bedrock:*, no other services.

resource "aws_iam_role" "ai" {
  name                 = "${var.name}-ai-pod-role"
  assume_role_policy   = data.aws_iam_policy_document.irsa_trust["ai"].json
  max_session_duration = 3600
  tags                 = merge(var.tags, { Workload = "ai" })
}

data "aws_iam_policy_document" "ai" {
  statement {
    sid    = "InvokeBedrockModels"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = var.bedrock_model_arns
  }
}

resource "aws_iam_role_policy" "ai" {
  name   = "${var.name}-ai-pod-policy"
  role   = aws_iam_role.ai.id
  policy = data.aws_iam_policy_document.ai.json
}
