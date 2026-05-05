resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = "AI Release Gate"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "iamwillsoto"
  }
}
data "aws_caller_identity" "current" {}
