variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.medium"
}

variable "db_username" {
  type    = string
  default = "nexgrad_prod_admin"
}

variable "alert_email" {
  type    = string
  default = "karthiksn20112004@gmail.com"
}

