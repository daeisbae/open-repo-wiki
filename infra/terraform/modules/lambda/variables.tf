# Lambda Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
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

variable "step_functions_arn" {
  description = "ARN of the Step Functions state machine"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.11"
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "max_concurrent_jobs" {
  description = "Maximum number of concurrent jobs"
  type        = number
  default     = 10
}

variable "lambda_log_level" {
  description = "Log level for Lambda functions"
  type        = string
  default     = "INFO"
}

# Jobs handler configuration
variable "jobs_handler_handler" {
  description = "Handler for jobs Lambda function"
  type        = string
  default     = "services.api.lambda_handler.jobs_handler"
}

variable "jobs_handler_package_path" {
  description = "Local path to jobs handler deployment package"
  type        = string
  default     = ""
}

variable "jobs_handler_s3_key" {
  description = "S3 key for jobs handler deployment package"
  type        = string
  default     = "lambda/jobs-handler.zip"
}

variable "jobs_handler_source_hash" {
  description = "Source code hash for jobs handler"
  type        = string
  default     = null
}

# Repos handler configuration
variable "repos_handler_handler" {
  description = "Handler for repos Lambda function"
  type        = string
  default     = "services.api.lambda_handler.repos_handler"
}

variable "repos_handler_package_path" {
  description = "Local path to repos handler deployment package"
  type        = string
  default     = ""
}

variable "repos_handler_s3_key" {
  description = "S3 key for repos handler deployment package"
  type        = string
  default     = "lambda/repos-handler.zip"
}

variable "repos_handler_source_hash" {
  description = "Source code hash for repos handler"
  type        = string
  default     = null
}

# S3 bucket for Lambda packages
variable "lambda_s3_bucket" {
  description = "S3 bucket for Lambda deployment packages"
  type        = string
  default     = ""
}

# API Gateway integration
variable "api_gateway_execution_arn" {
  description = "Execution ARN of API Gateway (for Lambda permissions)"
  type        = string
  default     = ""
}

variable "create_api_gateway_permissions" {
  description = "Whether to create API Gateway invoke permissions for Lambda"
  type        = bool
  default     = true
}

variable "additional_env_vars" {
  description = "Additional environment variables for Lambda functions"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
