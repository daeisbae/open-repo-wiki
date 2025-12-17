# Lambda Module Outputs

# Jobs Handler outputs
output "jobs_handler_arn" {
  description = "ARN of the jobs handler Lambda function"
  value       = aws_lambda_function.jobs_handler.arn
}

output "jobs_handler_name" {
  description = "Name of the jobs handler Lambda function"
  value       = aws_lambda_function.jobs_handler.function_name
}

output "jobs_handler_invoke_arn" {
  description = "Invoke ARN of the jobs handler Lambda function"
  value       = aws_lambda_function.jobs_handler.invoke_arn
}

output "jobs_handler_log_group_name" {
  description = "CloudWatch Log Group name for jobs handler"
  value       = aws_cloudwatch_log_group.jobs_handler.name
}

output "jobs_handler_log_group_arn" {
  description = "CloudWatch Log Group ARN for jobs handler"
  value       = aws_cloudwatch_log_group.jobs_handler.arn
}

# Repos Handler outputs
output "repos_handler_arn" {
  description = "ARN of the repos handler Lambda function"
  value       = aws_lambda_function.repos_handler.arn
}

output "repos_handler_name" {
  description = "Name of the repos handler Lambda function"
  value       = aws_lambda_function.repos_handler.function_name
}

output "repos_handler_invoke_arn" {
  description = "Invoke ARN of the repos handler Lambda function"
  value       = aws_lambda_function.repos_handler.invoke_arn
}

output "repos_handler_log_group_name" {
  description = "CloudWatch Log Group name for repos handler"
  value       = aws_cloudwatch_log_group.repos_handler.name
}

output "repos_handler_log_group_arn" {
  description = "CloudWatch Log Group ARN for repos handler"
  value       = aws_cloudwatch_log_group.repos_handler.arn
}
