# CloudWatch Alarms Module - Variables

# =============================================================================
# Common Variables
# =============================================================================

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# Step Functions Variables (Requirements 11.3)
# =============================================================================

variable "step_functions_arn" {
  description = "ARN of the Step Functions state machine to monitor"
  type        = string
}

variable "sfn_alarm_evaluation_periods" {
  description = "Number of periods to evaluate for Step Functions alarms"
  type        = number
  default     = 1
}

variable "sfn_alarm_period" {
  description = "Period in seconds for Step Functions alarm metrics"
  type        = number
  default     = 300 # 5 minutes
}

variable "sfn_failed_threshold" {
  description = "Threshold for Step Functions execution failed alarm"
  type        = number
  default     = 1
}

variable "sfn_timeout_threshold" {
  description = "Threshold for Step Functions execution timeout alarm"
  type        = number
  default     = 1
}

# =============================================================================
# ECS Variables (Requirements 11.4)
# =============================================================================

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster to monitor"
  type        = string
}

variable "ecs_task_family" {
  description = "Task definition family name for ECS task monitoring"
  type        = string
}

variable "ecs_log_group_name" {
  description = "CloudWatch Log Group name for ECS tasks"
  type        = string
}

variable "ecs_alarm_evaluation_periods" {
  description = "Number of periods to evaluate for ECS alarms"
  type        = number
  default     = 1
}

variable "ecs_alarm_period" {
  description = "Period in seconds for ECS alarm metrics"
  type        = number
  default     = 300 # 5 minutes
}

variable "ecs_failed_threshold" {
  description = "Threshold for ECS task failed alarm"
  type        = number
  default     = 1
}

variable "enable_log_metric_filters" {
  description = "Enable CloudWatch Log metric filters for ECS task monitoring"
  type        = bool
  default     = false
}

# =============================================================================
# API Gateway Variables (Requirements 11.5)
# =============================================================================

variable "api_gateway_name" {
  description = "Name of the API Gateway to monitor"
  type        = string
}

variable "api_gateway_stage" {
  description = "Stage name of the API Gateway to monitor"
  type        = string
}

variable "api_alarm_evaluation_periods" {
  description = "Number of periods to evaluate for API Gateway alarms"
  type        = number
  default     = 2
}

variable "api_alarm_period" {
  description = "Period in seconds for API Gateway alarm metrics"
  type        = number
  default     = 60 # 1 minute
}

variable "api_5xx_threshold" {
  description = "Threshold for API Gateway 5xx error count alarm"
  type        = number
  default     = 5
}

variable "api_5xx_rate_threshold" {
  description = "Threshold percentage for API Gateway 5xx error rate alarm"
  type        = number
  default     = 5 # 5%
}

variable "api_4xx_threshold" {
  description = "Threshold for API Gateway 4xx error count alarm"
  type        = number
  default     = 50
}

variable "api_latency_threshold" {
  description = "Threshold in milliseconds for API Gateway p95 latency alarm"
  type        = number
  default     = 5000 # 5 seconds
}

variable "enable_4xx_alarm" {
  description = "Enable 4xx error alarm for API Gateway"
  type        = bool
  default     = false
}

variable "enable_latency_alarm" {
  description = "Enable latency alarm for API Gateway"
  type        = bool
  default     = false
}
