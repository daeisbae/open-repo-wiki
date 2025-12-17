# API Gateway Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "v1"
}

# Lambda Integration ARNs
variable "jobs_handler_invoke_arn" {
  description = "Invoke ARN of the jobs handler Lambda function"
  type        = string
}

variable "repos_handler_invoke_arn" {
  description = "Invoke ARN of the repos handler Lambda function"
  type        = string
}

# Logging Configuration
variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "enable_access_logs" {
  description = "Enable API Gateway access logs (doesn't require account-level role)"
  type        = bool
  default     = true
}

variable "logging_level" {
  description = "API Gateway execution logging level (OFF, ERROR, INFO). Note: ERROR/INFO require account-level CloudWatch role"
  type        = string
  default     = "OFF"
}

variable "data_trace_enabled" {
  description = "Enable full request/response logging"
  type        = bool
  default     = false
}

# Throttling Configuration
variable "throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 100
}

variable "throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 50
}

# API Gateway Account Settings
variable "create_api_gateway_account" {
  description = "Whether to create API Gateway account settings (only needed once per region)"
  type        = bool
  default     = false
}

variable "api_gateway_cloudwatch_role_arn" {
  description = "ARN of IAM role for API Gateway to write CloudWatch Logs"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
