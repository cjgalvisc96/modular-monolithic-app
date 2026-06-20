terraform {
  # State backend is configured by Terragrunt (remote_state generation).
  # When running plain Terraform, supply -backend-config or fill these in.
  backend "s3" {
    # bucket         = "todo-app-tfstate-dev"
    # key            = "dev/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "todo-app-tflock-dev"
    # encrypt        = true
  }
}
