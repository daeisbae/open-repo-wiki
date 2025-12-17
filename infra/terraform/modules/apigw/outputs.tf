# API Gateway Module Outputs

output "rest_api_id" {
  description = "ID of the REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "rest_api_arn" {
  description = "ARN of the REST API"
  value       = aws_api_gateway_rest_api.main.arn
}

output "rest_api_name" {
  description = "Name of the REST API"
  value       = aws_api_gateway_rest_api.main.name
}

output "execution_arn" {
  description = "Execution ARN of the REST API (for Lambda permissions)"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "stage_name" {
  description = "Name of the deployed stage"
  value       = aws_api_gateway_stage.main.stage_name
}

output "stage_arn" {
  description = "ARN of the deployed stage"
  value       = aws_api_gateway_stage.main.arn
}

output "invoke_url" {
  description = "Base URL for API invocation"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "access_log_group_name" {
  description = "CloudWatch Log Group name for API access logs"
  value       = length(aws_cloudwatch_log_group.api_access_logs) > 0 ? aws_cloudwatch_log_group.api_access_logs[0].name : null
}

output "access_log_group_arn" {
  description = "CloudWatch Log Group ARN for API access logs"
  value       = length(aws_cloudwatch_log_group.api_access_logs) > 0 ? aws_cloudwatch_log_group.api_access_logs[0].arn : null
}

# Resource IDs for WAF association
output "jobs_resource_id" {
  description = "Resource ID of /jobs endpoint"
  value       = aws_api_gateway_resource.jobs.id
}

output "repos_resource_id" {
  description = "Resource ID of /repos endpoint"
  value       = aws_api_gateway_resource.repos.id
}
