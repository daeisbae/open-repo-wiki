# Secrets Manager Module Variables

variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "recovery_window_in_days" {
  description = "Number of days before a secret can be deleted (0 for immediate deletion)"
  type        = number
  default     = 7
}

variable "create_initial_versions" {
  description = "Whether to create initial secret versions with placeholder values"
  type        = bool
  default     = true
}

variable "github_token_value" {
  description = "GitHub token value (leave empty for placeholder)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "llm_api_key_value" {
  description = "LLM API key value (leave empty for placeholder)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
