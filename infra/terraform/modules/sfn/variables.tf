# Step Functions Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  type        = string
}

variable "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  type        = string
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "task_timeout_seconds" {
  description = "Timeout for the ECS task in seconds (default: 1 hour)"
  type        = number
  default     = 3600
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "log_level" {
  description = "Step Functions logging level (OFF, ALL, ERROR, FATAL)"
  type        = string
  default     = "ERROR"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
