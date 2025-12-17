# CloudWatch Alarms Module - Outputs

# =============================================================================
# SNS Topic Outputs
# =============================================================================

output "alarms_sns_topic_arn" {
  description = "ARN of the SNS topic for alarm notifications"
  value       = aws_sns_topic.alarms.arn
}

output "alarms_sns_topic_name" {
  description = "Name of the SNS topic for alarm notifications"
  value       = aws_sns_topic.alarms.name
}

# =============================================================================
# Step Functions Alarm Outputs
# =============================================================================

output "sfn_execution_failed_alarm_arn" {
  description = "ARN of the Step Functions execution failed alarm"
  value       = aws_cloudwatch_metric_alarm.sfn_execution_failed.arn
}

output "sfn_execution_timed_out_alarm_arn" {
  description = "ARN of the Step Functions execution timed out alarm"
  value       = aws_cloudwatch_metric_alarm.sfn_execution_timed_out.arn
}

# =============================================================================
# ECS Alarm Outputs
# =============================================================================

output "ecs_task_failed_alarm_arn" {
  description = "ARN of the ECS task failed alarm"
  value       = aws_cloudwatch_metric_alarm.ecs_task_failed.arn
}

output "ecs_task_stopped_error_alarm_arn" {
  description = "ARN of the ECS task stopped with error alarm (if enabled)"
  value       = var.enable_log_metric_filters ? aws_cloudwatch_metric_alarm.ecs_task_stopped_error[0].arn : null
}

# =============================================================================
# API Gateway Alarm Outputs
# =============================================================================

output "api_5xx_errors_alarm_arn" {
  description = "ARN of the API Gateway 5xx errors alarm"
  value       = aws_cloudwatch_metric_alarm.api_5xx_errors.arn
}

output "api_5xx_error_rate_alarm_arn" {
  description = "ARN of the API Gateway 5xx error rate alarm"
  value       = aws_cloudwatch_metric_alarm.api_5xx_error_rate.arn
}

output "api_4xx_errors_alarm_arn" {
  description = "ARN of the API Gateway 4xx errors alarm (if enabled)"
  value       = var.enable_4xx_alarm ? aws_cloudwatch_metric_alarm.api_4xx_errors[0].arn : null
}

output "api_latency_alarm_arn" {
  description = "ARN of the API Gateway latency alarm (if enabled)"
  value       = var.enable_latency_alarm ? aws_cloudwatch_metric_alarm.api_latency[0].arn : null
}

# =============================================================================
# Summary Outputs
# =============================================================================

output "all_alarm_arns" {
  description = "List of all alarm ARNs created by this module"
  value = compact([
    aws_cloudwatch_metric_alarm.sfn_execution_failed.arn,
    aws_cloudwatch_metric_alarm.sfn_execution_timed_out.arn,
    aws_cloudwatch_metric_alarm.ecs_task_failed.arn,
    var.enable_log_metric_filters ? aws_cloudwatch_metric_alarm.ecs_task_stopped_error[0].arn : null,
    aws_cloudwatch_metric_alarm.api_5xx_errors.arn,
    aws_cloudwatch_metric_alarm.api_5xx_error_rate.arn,
    var.enable_4xx_alarm ? aws_cloudwatch_metric_alarm.api_4xx_errors[0].arn : null,
    var.enable_latency_alarm ? aws_cloudwatch_metric_alarm.api_latency[0].arn : null,
  ])
}
