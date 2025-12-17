# CloudFront Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# S3 Origin Configuration
variable "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  type        = string
}

variable "s3_bucket_id" {
  description = "ID of the S3 bucket"
  type        = string
}

variable "create_s3_bucket_policy" {
  description = "Whether to create S3 bucket policy for CloudFront access"
  type        = bool
  default     = true
}

# Cache Configuration
variable "min_ttl" {
  description = "Minimum TTL for cached objects"
  type        = number
  default     = 0
}

variable "default_ttl" {
  description = "Default TTL for cached objects"
  type        = number
  default     = 86400 # 1 day
}


variable "max_ttl" {
  description = "Maximum TTL for cached objects"
  type        = number
  default     = 31536000 # 1 year
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # US, Canada, Europe
}

# SSL/TLS Configuration
variable "acm_certificate_arn" {
  description = "ARN of ACM certificate for custom domain"
  type        = string
  default     = ""
}

variable "domain_aliases" {
  description = "List of custom domain aliases"
  type        = list(string)
  default     = []
}

# Geo Restrictions
variable "geo_restriction_type" {
  description = "Geo restriction type (none, whitelist, blacklist)"
  type        = string
  default     = "none"
}

variable "geo_restriction_locations" {
  description = "List of country codes for geo restriction"
  type        = list(string)
  default     = []
}

# WAF Configuration
variable "web_acl_arn" {
  description = "ARN of WAF Web ACL to associate"
  type        = string
  default     = null
}

# Logging Configuration
variable "enable_logging" {
  description = "Enable CloudFront access logging"
  type        = bool
  default     = false
}

variable "logging_bucket" {
  description = "S3 bucket for CloudFront access logs"
  type        = string
  default     = ""
}

variable "logging_prefix" {
  description = "Prefix for CloudFront access logs"
  type        = string
  default     = "cloudfront/"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
