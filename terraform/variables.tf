variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for infrastructure deployment"
}

variable "project_name" {
  type        = string
  default     = "aws-ai-security-shield"
  description = "Name of the project and resource naming prefix"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment identifier (dev, staging, prod)"
}
