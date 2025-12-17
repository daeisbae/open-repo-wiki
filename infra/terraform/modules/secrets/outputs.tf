# Secrets Manager Module Outputs

output "github_token_secret_arn" {
  description = "ARN of the GitHub token secret"
  value       = aws_secretsmanager_secret.github_token.arn
}

output "github_token_secret_name" {
  description = "Name of the GitHub token secret"
  value       = aws_secretsmanager_secret.github_token.name
}

output "llm_api_key_secret_arn" {
  description = "ARN of the LLM API key secret"
  value       = aws_secretsmanager_secret.llm_api_key.arn
}

output "llm_api_key_secret_name" {
  description = "Name of the LLM API key secret"
  value       = aws_secretsmanager_secret.llm_api_key.name
}

output "all_secret_arns" {
  description = "List of all secret ARNs for IAM policies"
  value = [
    aws_secretsmanager_secret.github_token.arn,
    aws_secretsmanager_secret.llm_api_key.arn
  ]
}

# ECS secrets configuration format for task definition
output "ecs_secrets_config" {
  description = "Secrets configuration for ECS task definition"
  value = [
    {
      name      = "GITHUB_TOKEN"
      valueFrom = aws_secretsmanager_secret.github_token.arn
    },
    {
      name      = "LLM_APIKEY"
      valueFrom = aws_secretsmanager_secret.llm_api_key.arn
    }
  ]
}
