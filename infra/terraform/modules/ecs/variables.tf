# ECS Module Variables

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

variable "vpc_id" {
  description = "VPC ID for ECS tasks"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecr_repository_url" {
  description = "URL of the ECR repository for processor image"
  type        = string
}

variable "processor_image_tag" {
  description = "Docker image tag for the processor"
  type        = string
  default     = "latest"
}

variable "dynamodb_main_table_name" {
  description = "Name of the DynamoDB main table"
  type        = string
}

variable "dynamodb_jobs_table_name" {
  description = "Name of the DynamoDB jobs table"
  type        = string
}

variable "s3_artifacts_bucket_name" {
  description = "Name of the S3 artifacts bucket"
  type        = string
}



variable "llm_provider" {
  description = "LLM provider name (deepseek, openrouter)"
  type        = string
  default     = "deepseek"
}

variable "llm_model_name" {
  description = "LLM model name"
  type        = string
  default     = "deepseek-chat"
}

variable "task_cpu" {
  description = "CPU units for the Fargate task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Memory (MB) for the Fargate task"
  type        = number
  default     = 2048
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "enable_health_check" {
  description = "Enable container health check"
  type        = bool
  default     = false
}

variable "use_fargate_spot" {
  description = "Use Fargate Spot for cost savings"
  type        = bool
  default     = false
}

variable "secrets_config" {
  description = "List of secrets to inject from Secrets Manager"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

variable "cpu_architecture" {
  description = "CPU architecture for Fargate tasks (X86_64 or ARM64)"
  type        = string
  default     = "ARM64"

  validation {
    condition     = contains(["X86_64", "ARM64"], var.cpu_architecture)
    error_message = "cpu_architecture must be either X86_64 or ARM64"
  }
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
