variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "vpc_cidr" {
  type        = string
  description = "CIDR block of the VPC for internal service access"
  default     = "10.100.0.0/16"
}

