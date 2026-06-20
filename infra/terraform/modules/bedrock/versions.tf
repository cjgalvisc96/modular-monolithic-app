terraform {
  required_version = ">= 1.5"

  required_providers {
    # Pin to AWS 5.x like the rest of the stack. (On 6.x,
    # data.aws_region.current.name is deprecated in favor of .region; pinning
    # 5.x keeps a single, consistent provider major across all modules.)
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
