variable "aws_region" {
  description = "AWS region used for the AI Release Gate system."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base project name used for AWS resource naming."
  type        = string
  default     = "ai-release-gate"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}