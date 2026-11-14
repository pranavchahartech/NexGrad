# ==============================================================================
# NexGrad Terraform Root Configuration
# Resources: AWS EC2 (3 instances), AWS IAM (SSM Profiles), Amazon VPC & Security Groups
# Explicitly Excluded: S3, RDS, ALB, NAT Gateway, EFS, Route53, CloudWatch
# ==============================================================================

module "vpc" {
  source              = "./modules/vpc"
  project_name        = var.project_name
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
}

module "security" {
  source       = "./modules/security"
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
}

module "iam" {
  source       = "./modules/iam"
  project_name = var.project_name
  environment  = var.environment
}

module "ec2" {
  source                  = "./modules/ec2"
  project_name            = var.project_name
  environment             = var.environment
  instance_type           = var.instance_type
  public_subnet_id        = module.vpc.public_subnet_ids[0]
  backend_subnet_id       = module.vpc.public_subnet_ids[0]
  management_subnet_id    = module.vpc.public_subnet_ids[0]
  frontend_sg_id          = module.security.frontend_sg_id
  backend_sg_id           = module.security.backend_sg_id
  management_sg_id        = module.security.management_sg_id
  target_profile_name     = module.iam.target_profile_name
  management_profile_name = module.iam.management_profile_name
}
