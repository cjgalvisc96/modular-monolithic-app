# RBAC groups. The pre-token Lambda maps the highest-privilege group into a
# `role` claim; group membership is also surfaced verbatim in the `groups` claim.

resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.this.id
  description  = "Tenant administrators — full management within their tenant."
  precedence   = 1
}

resource "aws_cognito_user_group" "member" {
  name         = "member"
  user_pool_id = aws_cognito_user_pool.this.id
  description  = "Standard members — day-to-day TODO operations within their tenant."
  precedence   = 10
}
