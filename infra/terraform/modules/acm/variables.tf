# ACM Module Variables

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
  description = "Primary domain name for the certificate"
  type        = string
}

variable "include_www" {
  description = "Include www subdomain in the certificate"
  type        = bool
  default     = true
}

variable "additional_domains" {
  description = "Additional domain names to include in the certificate"
  type        = list(string)
  default     = []
}

# Validation Configuration
variable "create_validation_records" {
  description = "Create Route53 validation records automatically"
  type        = bool
  default     = true
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID (if already created elsewhere)"
  type        = string
  default     = ""
}

variable "use_existing_zone_id" {
  description = "Whether to use the provided route53_zone_id instead of looking up"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
