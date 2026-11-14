output "production_frontend_public_ip" {
  description = "Public IP of NexGrad Frontend Nginx instance"
  value       = module.nexgrad_prod.frontend_public_ip
}

output "production_frontend_private_ip" {
  description = "VPC Private IP of Frontend instance"
  value       = module.nexgrad_prod.frontend_private_ip
}

output "production_backend_public_ip" {
  description = "Public IP of Backend instance (outbound without NAT)"
  value       = module.nexgrad_prod.backend_public_ip
}

output "production_backend_private_ip" {
  description = "VPC Private IP of Backend instance (Django + DB)"
  value       = module.nexgrad_prod.backend_private_ip
}

output "production_management_public_ip" {
  description = "Public IP of DevOps Management instance (outbound without NAT)"
  value       = module.nexgrad_prod.management_public_ip
}

output "production_management_private_ip" {
  description = "VPC Private IP of DevOps Management instance"
  value       = module.nexgrad_prod.management_private_ip
}

output "production_instance_ids" {
  description = "All three production EC2 instance IDs"
  value       = module.nexgrad_prod.instance_ids
}
