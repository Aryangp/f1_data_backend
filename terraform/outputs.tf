output "instance_public_ip" {
  description = "Public Elastic IP address of the EC2 instance"
  value       = aws_eip.f1_eip.public_ip
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.f1_app_repo.repository_url
}

output "private_key_pem" {
  description = "Private key for SSH access. SAVE THIS SECURELY!"
  value       = tls_private_key.pk.private_key_pem
  sensitive   = true
}
