# WAF Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "scope" {
  description = "WAF scope (REGIONAL for API Gateway, CLOUDFRONT for CloudFront)"
  type        = string
  default     = "REGIONAL"

  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.scope)
    error_message = "Scope must be either REGIONAL or CLOUDFRONT."
  }
}

# Rate Limiting Configuration
variable "jobs_create_rate_limit" {
  description = "Rate limit for POST /jobs (job creation) per 5 minutes per IP"
  type        = number
  default     = 20  # Stricter limit for job creation
}

variable "jobs_poll_rate_limit" {
  description = "Rate limit for GET /jobs/{id} (polling) per 5 minutes per IP"
  type        = number
  default     = 300  # Higher limit for polling (3s interval = 100 requests/5min per job)
}

variable "global_rate_limit" {
  description = "Global rate limit (requests per 5 minutes per IP)"
  type        = number
  default     = 2000
}

# Rule Exclusions
variable "common_ruleset_excluded_rules" {
  description = "List of rules to exclude from CommonRuleSet"
  type        = list(string)
  default     = []
}

# IP Blocking
variable "blocked_ip_addresses" {
  description = "List of IP addresses to block (CIDR notation)"
  type        = list(string)
  default     = []
}


# Association Configuration
variable "api_gateway_stage_arn" {
  description = "ARN of API Gateway stage to associate with WAF"
  type        = string
  default     = ""
}

variable "associate_api_gateway" {
  description = "Whether to associate WAF with API Gateway stage"
  type        = bool
  default     = true
}

# Logging Configuration
variable "enable_logging" {
  description = "Enable WAF logging to CloudWatch"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 30
}

variable "redacted_fields" {
  description = "List of fields to redact from logs"
  type = list(object({
    type = string
    name = string
  }))
  default = [
    {
      type = "single_header"
      name = "authorization"
    }
  ]
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
