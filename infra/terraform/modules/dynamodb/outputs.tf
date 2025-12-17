# DynamoDB Module Outputs

output "main_table_name" {
  description = "Name of the main DynamoDB table"
  value       = aws_dynamodb_table.main.name
}

output "main_table_arn" {
  description = "ARN of the main DynamoDB table"
  value       = aws_dynamodb_table.main.arn
}

output "jobs_table_name" {
  description = "Name of the jobs DynamoDB table"
  value       = aws_dynamodb_table.jobs.name
}

output "jobs_table_arn" {
  description = "ARN of the jobs DynamoDB table"
  value       = aws_dynamodb_table.jobs.arn
}

output "jobs_status_index_name" {
  description = "Name of the status GSI on jobs table"
  value       = "StatusIndex"
}
