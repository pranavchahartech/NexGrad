output "vpc_id" {
  description = "ID of the provisioned VPC"
  value       = module.vpc.vpc_id
}

output "frontend_public_ip" {
  description = "Public IP address of Frontend EC2 instance (Nginx)"
  value       = module.ec2.frontend_public_ip
}

output "frontend_private_ip" {
  description = "Private IP address of Frontend EC2 instance"
  value       = module.ec2.frontend_private_ip
}

output "backend_public_ip" {
  description = "Public IP address of Backend EC2 instance (direct outbound internet without NAT)"
  value       = module.ec2.backend_public_ip
}

output "backend_private_ip" {
  description = "Private IP address of Backend EC2 instance (Django + DB)"
  value       = module.ec2.backend_private_ip
}

output "management_public_ip" {
  description = "Public IP address of DevOps Management EC2 instance (direct outbound SSM without NAT)"
  value       = module.ec2.management_public_ip
}

output "management_private_ip" {
  description = "Private IP address of DevOps Management EC2 instance (Ansible/Puppet/Nagios)"
  value       = module.ec2.management_private_ip
}

output "instance_ids" {
  description = "List of all three EC2 instance IDs"
  value       = module.ec2.instance_ids
}
