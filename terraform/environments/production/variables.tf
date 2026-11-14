variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "volume_size" {
  type    = number
  default = 8
}

variable "db_username" {
  type    = string
  default = "nexgrad_prod_admin"
}

variable "alert_email" {
  type    = string
  default = "karthiksn20112004@gmail.com"
}

