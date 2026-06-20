aws_region            = "us-east-1"
environment           = "dev"
project               = "todo-app"
owner                 = "platform-team"
domain_name           = "dev.todo-app.example.com"
cognito_domain_prefix = "todo-app-dev"

bedrock_model_ids = [
  "anthropic.claude-3-haiku-20240307-v1:0",
]

# db_master_password is sensitive — supply via TF_VAR_db_master_password or a
# secret manager, never commit it here.
