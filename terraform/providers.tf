provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "NexGrad"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Platform    = "DevOps-Automation-SelfHealing"
    }
  }
}

