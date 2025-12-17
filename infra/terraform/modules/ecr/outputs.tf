# ECR Module Outputs

output "repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.processor.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.processor.arn
}

output "repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.processor.name
}

output "registry_id" {
  description = "Registry ID where the repository was created"
  value       = aws_ecr_repository.processor.registry_id
}
