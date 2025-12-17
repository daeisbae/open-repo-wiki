# Route53 Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# Domain Configuration
variable "domain_name" {
  description = "Root domain name (e.g., openrepowiki.xyz)"
  type        = string
}

variable "subdomain" {
  description = "Subdomain for the application (empty for apex domain)"
  type        = string
  default     = ""
}

variable "create_hosted_zone" {
  description = "Whether to create a new hosted zone or use existing"
  type        = bool
  default     = false
}

# CloudFront Configuration
variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
  default     = ""
}

variable "create_cloudfront_records" {
  description = "Whether to create CloudFront DNS records"
  type        = bool
  default     = true
}

variable "cloudfront_hosted_zone_id" {
  description = "CloudFront hosted zone ID (always Z2FDTNDATAQYW2)"
  type        = string
  default     = "Z2FDTNDATAQYW2"
}

# API Gateway Configuration (optional)
variable "api_domain_name" {
  description = "API Gateway custom domain name"
  type        = string
  default     = ""
}

variable "api_subdomain" {
  description = "Subdomain for API (default: api)"
  type        = string
  default     = "api"
}

variable "api_hosted_zone_id" {
  description = "API Gateway regional hosted zone ID"
  type        = string
  default     = ""
}

# WWW Redirect
variable "create_www_redirect" {
  description = "Create www subdomain redirect to apex"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
