output "frontend_instance_id" {
  value = aws_instance.frontend.id
}

output "frontend_public_ip" {
  value = aws_instance.frontend.public_ip
}

output "frontend_private_ip" {
  value = aws_instance.frontend.private_ip
}

output "backend_instance_id" {
  value = aws_instance.backend.id
}

output "backend_public_ip" {
  value = aws_instance.backend.public_ip
}

output "backend_private_ip" {
  value = aws_instance.backend.private_ip
}

output "management_instance_id" {
  value = aws_instance.management.id
}

output "management_public_ip" {
  value = aws_instance.management.public_ip
}

output "management_private_ip" {
  value = aws_instance.management.private_ip
}

output "instance_ids" {
  value = [
    aws_instance.frontend.id,
    aws_instance.backend.id,
    aws_instance.management.id
  ]
}
