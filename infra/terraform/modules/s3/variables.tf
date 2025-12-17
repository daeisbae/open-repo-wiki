# S3 Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning for the S3 bucket"
  type        = bool
  default     = true
}

variable "enable_lifecycle_rules" {
  description = "Enable lifecycle rules for cleanup"
  type        = bool
  default     = true
}

variable "noncurrent_version_expiration_days" {
  description = "Days after which noncurrent versions are deleted"
  type        = number
  default     = 90
}

variable "cloudfront_distribution_arn" {
  description = "ARN of CloudFront distribution for bucket policy (optional)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
