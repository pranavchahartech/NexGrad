variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Target environment (production/staging)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance size"
  type        = string
  default     = "t3.micro"
}

variable "volume_size" {
  description = "EBS root volume size in GB"
  type        = number
  default     = 8
}

variable "public_subnet_id" {
  description = "Subnet ID for Frontend EC2 instance (public)"
  type        = string
}

variable "backend_subnet_id" {
  description = "Subnet ID for Backend EC2 instance"
  type        = string
}

variable "management_subnet_id" {
  description = "Subnet ID for Management EC2 instance"
  type        = string
}

variable "frontend_sg_id" {
  description = "Security Group ID for Frontend EC2"
  type        = string
}

variable "backend_sg_id" {
  description = "Security Group ID for Backend EC2"
  type        = string
}

variable "management_sg_id" {
  description = "Security Group ID for Management EC2"
  type        = string
}

variable "target_profile_name" {
  description = "IAM instance profile name for target instances"
  type        = string
}

variable "management_profile_name" {
  description = "IAM instance profile name for management controller"
  type        = string
}
