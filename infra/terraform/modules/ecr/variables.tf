# ECR Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "image_tag_mutability" {
  description = "Image tag mutability setting (MUTABLE or IMMUTABLE)"
  type        = string
  default     = "MUTABLE"
}

variable "scan_on_push" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of KMS key for encryption (optional, uses AWS managed key if not provided)"
  type        = string
  default     = ""
}

variable "max_image_count" {
  description = "Maximum number of images to keep in repository"
  type        = number
  default     = 30
}

variable "allowed_account_ids" {
  description = "List of AWS account IDs allowed to pull images (for cross-account access)"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
