# Route53 Module - DNS Configuration
# Manages DNS records for custom domain

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# Route53 Hosted Zone (optional - use existing or create new)
# =============================================================================

data "aws_route53_zone" "main" {
  count        = var.create_hosted_zone ? 0 : 1
  name         = var.domain_name
  private_zone = false
}

resource "aws_route53_zone" "main" {
  count = var.create_hosted_zone ? 1 : 0
  name  = var.domain_name

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-zone"
  })
}

locals {
  zone_id = var.create_hosted_zone ? aws_route53_zone.main[0].zone_id : data.aws_route53_zone.main[0].zone_id
}

# =============================================================================
# A Record - CloudFront Distribution (IPv4)
# =============================================================================

resource "aws_route53_record" "cloudfront_a" {
  count   = var.create_cloudfront_records ? 1 : 0
  zone_id = local.zone_id
  name    = var.subdomain != "" ? "${var.subdomain}.${var.domain_name}" : var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# =============================================================================
# AAAA Record - CloudFront Distribution (IPv6)
# =============================================================================

resource "aws_route53_record" "cloudfront_aaaa" {
  count   = var.create_cloudfront_records ? 1 : 0
  zone_id = local.zone_id
  name    = var.subdomain != "" ? "${var.subdomain}.${var.domain_name}" : var.domain_name
  type    = "AAAA"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

# =============================================================================
# API Gateway Custom Domain (optional)
# =============================================================================

resource "aws_route53_record" "api" {
  count   = var.api_domain_name != "" ? 1 : 0
  zone_id = local.zone_id
  name    = var.api_subdomain != "" ? "${var.api_subdomain}.${var.domain_name}" : "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.api_domain_name
    zone_id                = var.api_hosted_zone_id
    evaluate_target_health = false
  }
}

# =============================================================================
# WWW Redirect (optional)
# =============================================================================

resource "aws_route53_record" "www" {
  count   = var.create_www_redirect && var.create_cloudfront_records ? 1 : 0
  zone_id = local.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}
