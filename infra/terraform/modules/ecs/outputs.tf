# ECS Module Outputs

output "cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.main.id
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "task_definition_arn" {
  description = "ARN of the processor task definition"
  value       = aws_ecs_task_definition.processor.arn
}

output "task_definition_family" {
  description = "Family of the processor task definition"
  value       = aws_ecs_task_definition.processor.family
}

output "task_definition_revision" {
  description = "Revision of the processor task definition"
  value       = aws_ecs_task_definition.processor.revision
}

output "security_group_id" {
  description = "Security group ID for ECS tasks"
  value       = aws_security_group.ecs_tasks.id
}

output "log_group_name" {
  description = "CloudWatch Log Group name for processor"
  value       = aws_cloudwatch_log_group.processor.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN for processor"
  value       = aws_cloudwatch_log_group.processor.arn
}
