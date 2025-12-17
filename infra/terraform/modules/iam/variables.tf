# IAM Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "dynamodb_main_table_arn" {
  description = "ARN of the DynamoDB main table"
  type        = string
  default     = "*"
}

variable "dynamodb_jobs_table_arn" {
  description = "ARN of the DynamoDB jobs table"
  type        = string
  default     = "*"
}

variable "s3_artifacts_bucket_arn" {
  description = "ARN of the S3 artifacts bucket"
  type        = string
  default     = "*"
}

variable "step_functions_arn" {
  description = "ARN of the Step Functions state machine"
  type        = string
  default     = "*"
}

variable "secrets_manager_arns" {
  description = "ARNs of Secrets Manager secrets"
  type        = list(string)
  default     = ["*"]
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
