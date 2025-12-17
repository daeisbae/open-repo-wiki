# Secrets Manager Module
# Requirements: 9.4 - Store secrets in AWS Secrets Manager for GitHub token and LLM API keys

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# GitHub Token Secret
# =============================================================================

resource "aws_secretsmanager_secret" "github_token" {
  name                    = "${local.name_prefix}/github-token"
  description             = "GitHub Personal Access Token for repository access"
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-github-token"
  })
}

# Initial secret version with placeholder value
# The actual value should be set manually or via CI/CD
resource "aws_secretsmanager_secret_version" "github_token" {
  count         = var.create_initial_versions ? 1 : 0
  secret_id     = aws_secretsmanager_secret.github_token.id
  secret_string = var.github_token_value != "" ? var.github_token_value : "PLACEHOLDER_REPLACE_ME"
}

# =============================================================================
# LLM API Key Secret (e.g., OpenRouter, DeepSeek)
# =============================================================================

resource "aws_secretsmanager_secret" "llm_api_key" {
  name                    = "${local.name_prefix}/llm-api-key"
  description             = "API key for LLM provider (OpenRouter, DeepSeek, etc.)"
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-llm-api-key"
  })
}

# Initial secret version with placeholder value
resource "aws_secretsmanager_secret_version" "llm_api_key" {
  count         = var.create_initial_versions ? 1 : 0
  secret_id     = aws_secretsmanager_secret.llm_api_key.id
  secret_string = var.llm_api_key_value != "" ? var.llm_api_key_value : "PLACEHOLDER_REPLACE_ME"
}
