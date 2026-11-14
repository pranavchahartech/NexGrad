# Production Environment Terraform Orchestration
module "nexgrad_prod" {
  source = "../../"

  environment         = "production"
  project_name        = "nexgrad"
  aws_region          = var.aws_region
  vpc_cidr            = "10.100.0.0/16"
  public_subnet_cidrs = ["10.100.1.0/24", "10.100.2.0/24"]
  instance_type       = var.instance_type
  volume_size         = var.volume_size
  db_name             = "nexgrad_production"
  db_username         = var.db_username
}

