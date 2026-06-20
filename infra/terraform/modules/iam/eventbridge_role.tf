# EventBridge publisher IRSA role.
# Least-privilege: events:PutEvents to ONE specific bus only. No subscribe, no
# rule/target management, no other buses. Assumed by the API service account.

resource "aws_iam_role" "eventbridge" {
  name                 = "${var.name}-eventbridge-publisher-role"
  assume_role_policy   = data.aws_iam_policy_document.irsa_trust["api"].json
  max_session_duration = 3600
  tags                 = merge(var.tags, { Workload = "eventbridge-publisher" })
}

data "aws_iam_policy_document" "eventbridge" {
  statement {
    sid       = "PublishToBusOnly"
    effect    = "Allow"
    actions   = ["events:PutEvents"]
    resources = [var.eventbridge_bus_arn]
  }
}

resource "aws_iam_role_policy" "eventbridge" {
  name   = "${var.name}-eventbridge-publisher-policy"
  role   = aws_iam_role.eventbridge.id
  policy = data.aws_iam_policy_document.eventbridge.json
}
