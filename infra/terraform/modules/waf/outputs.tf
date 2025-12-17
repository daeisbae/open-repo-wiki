# WAF Module Outputs

output "web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.id
}

output "web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.arn
}

output "web_acl_name" {
  description = "Name of the WAF Web ACL"
  value       = aws_wafv2_web_acl.main.name
}

output "web_acl_capacity" {
  description = "Capacity units used by the Web ACL"
  value       = aws_wafv2_web_acl.main.capacity
}

output "blocked_ip_set_arn" {
  description = "ARN of the blocked IP set (if created)"
  value       = length(aws_wafv2_ip_set.blocked) > 0 ? aws_wafv2_ip_set.blocked[0].arn : null
}

output "log_group_name" {
  description = "CloudWatch Log Group name for WAF logs"
  value       = var.enable_logging ? aws_cloudwatch_log_group.waf[0].name : null
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN for WAF logs"
  value       = var.enable_logging ? aws_cloudwatch_log_group.waf[0].arn : null
}
