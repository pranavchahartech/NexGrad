variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Target deployment environment (production/staging)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "nexgrad"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.100.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.100.1.0/24", "10.100.2.0/24"]
}

variable "instance_type" {
  description = "EC2 instance size for web and application servers"
  type        = string
  default     = "t3.micro"
}

variable "volume_size" {
  description = "EBS root volume size in GB for EC2 instances"
  type        = number
  default     = 8
}

variable "db_name" {
  description = "Production PostgreSQL database name on EC2-2"
  type        = string
  default     = "nexgrad_prod"
}

variable "db_username" {
  description = "Production PostgreSQL application username on EC2-2"
  type        = string
  default     = "nexgrad_admin"
}

variable "alert_email" {
  description = "DevOps & SRE alert notification email address"
  type        = string
  default     = "karthiksn20112004@gmail.com"
}

