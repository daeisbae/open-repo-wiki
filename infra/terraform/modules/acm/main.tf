# ACM Module - SSL/TLS Certificates
# Creates and validates ACM certificates for custom domains

terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.environment}"
  
  # Build list of domain names for the certificate
  domain_names = concat(
    [var.domain_name],
    var.include_www ? ["www.${var.domain_name}"] : [],
    var.additional_domains
  )
}

# =============================================================================
# ACM Certificate
# Note: For CloudFront, certificate MUST be in us-east-1
# =============================================================================

resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = slice(local.domain_names, 1, length(local.domain_names))
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-cert"
  })
}

# =============================================================================
# DNS Validation Records
# =============================================================================

data "aws_route53_zone" "main" {
  count        = var.create_validation_records && !var.use_existing_zone_id ? 1 : 0
  name         = var.domain_name
  private_zone = false
}

locals {
  zone_id = var.use_existing_zone_id ? var.route53_zone_id : (var.create_validation_records ? data.aws_route53_zone.main[0].zone_id : "")
}

resource "aws_route53_record" "validation" {
  for_each = var.create_validation_records ? {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = local.zone_id
}

# =============================================================================
# Certificate Validation
# =============================================================================

resource "aws_acm_certificate_validation" "main" {
  count                   = var.create_validation_records ? 1 : 0
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.validation : record.fqdn]
}
