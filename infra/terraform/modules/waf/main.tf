# WAF Module - Web Application Firewall
# Requirements: 9.6 - WAFv2 with CommonRuleSet, KnownBadInputs, and rate-based rules

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# WAF Web ACL (Requirements 9.6)
# =============================================================================

resource "aws_wafv2_web_acl" "main" {
  name        = "${local.name_prefix}-waf"
  description = "WAF Web ACL for OpenRepoWiki - ${var.environment}"
  scope       = var.scope # REGIONAL for API Gateway, CLOUDFRONT for CloudFront

  default_action {
    allow {}
  }

  # =============================================================================
  # AWS Managed Rules - Common Rule Set
  # =============================================================================

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        # Exclude rules that might cause false positives
        dynamic "rule_action_override" {
          for_each = var.common_ruleset_excluded_rules
          content {
            name = rule_action_override.value
            action_to_use {
              count {}
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }


  # =============================================================================
  # AWS Managed Rules - Known Bad Inputs
  # =============================================================================

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-known-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  # =============================================================================
  # Rate-Based Rule for POST /jobs (Job Creation)
  # Stricter limit to prevent abuse of job creation
  # =============================================================================

  rule {
    name     = "RateLimitJobCreation"
    priority = 3

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.jobs_create_rate_limit
        aggregate_key_type = "IP"

        scope_down_statement {
          and_statement {
            statement {
              byte_match_statement {
                search_string         = "/jobs"
                positional_constraint = "EXACTLY"

                field_to_match {
                  uri_path {}
                }

                text_transformation {
                  priority = 0
                  type     = "LOWERCASE"
                }
              }
            }
            statement {
              byte_match_statement {
                search_string         = "post"
                positional_constraint = "EXACTLY"

                field_to_match {
                  method {}
                }

                text_transformation {
                  priority = 0
                  type     = "LOWERCASE"
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit-job-create"
      sampled_requests_enabled   = true
    }
  }

  # =============================================================================
  # Rate-Based Rule for GET /jobs (Job Polling)
  # Higher limit since polling is read-only and expected behavior
  # =============================================================================

  rule {
    name     = "RateLimitJobPolling"
    priority = 4

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.jobs_poll_rate_limit
        aggregate_key_type = "IP"

        scope_down_statement {
          and_statement {
            statement {
              byte_match_statement {
                search_string         = "/jobs/"
                positional_constraint = "STARTS_WITH"

                field_to_match {
                  uri_path {}
                }

                text_transformation {
                  priority = 0
                  type     = "LOWERCASE"
                }
              }
            }
            statement {
              byte_match_statement {
                search_string         = "get"
                positional_constraint = "EXACTLY"

                field_to_match {
                  method {}
                }

                text_transformation {
                  priority = 0
                  type     = "LOWERCASE"
                }
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit-job-poll"
      sampled_requests_enabled   = true
    }
  }

  # =============================================================================
  # Global Rate Limit Rule
  # =============================================================================

  rule {
    name     = "GlobalRateLimit"
    priority = 5

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = var.global_rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-global-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  # =============================================================================
  # IP Block List (optional)
  # =============================================================================

  dynamic "rule" {
    for_each = length(var.blocked_ip_addresses) > 0 ? [1] : []
    content {
      name     = "BlockedIPAddresses"
      priority = 0

      action {
        block {}
      }

      statement {
        ip_set_reference_statement {
          arn = aws_wafv2_ip_set.blocked[0].arn
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-blocked-ips"
        sampled_requests_enabled   = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-waf"
  })
}

# =============================================================================
# IP Set for Blocked Addresses (optional)
# =============================================================================

resource "aws_wafv2_ip_set" "blocked" {
  count              = length(var.blocked_ip_addresses) > 0 ? 1 : 0
  name               = "${local.name_prefix}-blocked-ips"
  description        = "Blocked IP addresses"
  scope              = var.scope
  ip_address_version = "IPV4"
  addresses          = var.blocked_ip_addresses

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-blocked-ips"
  })
}


# =============================================================================
# WAF Association with API Gateway (Regional)
# =============================================================================

resource "aws_wafv2_web_acl_association" "api_gateway" {
  count        = var.scope == "REGIONAL" && var.associate_api_gateway ? 1 : 0
  resource_arn = var.api_gateway_stage_arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

# =============================================================================
# CloudWatch Log Group for WAF Logs
# =============================================================================

resource "aws_cloudwatch_log_group" "waf" {
  count             = var.enable_logging ? 1 : 0
  name              = "aws-waf-logs-${local.name_prefix}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "aws-waf-logs-${local.name_prefix}"
  })
}

# =============================================================================
# WAF Logging Configuration
# =============================================================================

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count                   = var.enable_logging ? 1 : 0
  log_destination_configs = [aws_cloudwatch_log_group.waf[0].arn]
  resource_arn            = aws_wafv2_web_acl.main.arn

  dynamic "redacted_fields" {
    for_each = var.redacted_fields
    content {
      dynamic "single_header" {
        for_each = redacted_fields.value.type == "single_header" ? [1] : []
        content {
          name = redacted_fields.value.name
        }
      }
    }
  }
}
