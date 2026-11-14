output "target_profile_name" {
  description = "IAM instance profile name for target instances (EC2-1 and EC2-2)"
  value       = aws_iam_instance_profile.target_profile.name
}

output "management_profile_name" {
  description = "IAM instance profile name for management controller (EC2-3)"
  value       = aws_iam_instance_profile.management_profile.name
}

