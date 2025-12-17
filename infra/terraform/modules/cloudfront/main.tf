# CloudFront Module - Static UI Distribution
# Requirements: 3.5 - CloudFront OAC for S3 access
# Requirements: 8.1 - Static UI hosting

locals {
  name_prefix  = "${var.project}-${var.environment}"
  s3_origin_id = "${local.name_prefix}-s3-origin"
}

# =============================================================================
# Origin Access Control (Requirements 3.5)
# =============================================================================

resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${local.name_prefix}-oac"
  description                       = "OAC for ${local.name_prefix} S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# =============================================================================
# CloudFront Distribution (Requirements 8.1)
# =============================================================================

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "OpenRepoWiki Static UI - ${var.environment}"
  default_root_object = "index.html"
  price_class         = var.price_class
  http_version        = "http2and3"

  # S3 Origin for static assets
  origin {
    domain_name              = var.s3_bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  # Default cache behavior for static assets
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = local.s3_origin_id

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = var.min_ttl
    default_ttl            = var.default_ttl
    max_ttl                = var.max_ttl
    compress               = true
  }

  # Cache behavior for HTML files (shorter TTL for updates)
  ordered_cache_behavior {
    path_pattern     = "*.html"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = local.s3_origin_id

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 300  # 5 minutes
    max_ttl                = 3600 # 1 hour
    compress               = true
  }


  # Custom error responses for SPA routing
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  # Geo restrictions
  restrictions {
    geo_restriction {
      restriction_type = var.geo_restriction_type
      locations        = var.geo_restriction_locations
    }
  }

  # SSL/TLS configuration
  viewer_certificate {
    cloudfront_default_certificate = var.acm_certificate_arn == "" ? true : false
    acm_certificate_arn            = var.acm_certificate_arn != "" ? var.acm_certificate_arn : null
    ssl_support_method             = var.acm_certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version       = var.acm_certificate_arn != "" ? "TLSv1.2_2021" : null
  }

  # Custom domain aliases
  aliases = var.domain_aliases

  # WAF association (if provided)
  web_acl_id = var.web_acl_arn

  # Logging configuration
  dynamic "logging_config" {
    for_each = var.enable_logging ? [1] : []
    content {
      include_cookies = false
      bucket          = var.logging_bucket
      prefix          = var.logging_prefix
    }
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-cloudfront"
  })
}

# =============================================================================
# S3 Bucket Policy for CloudFront OAC
# This policy allows CloudFront to access the S3 bucket
# =============================================================================

data "aws_iam_policy_document" "s3_policy" {
  statement {
    sid    = "AllowCloudFrontServicePrincipal"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${var.s3_bucket_arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "cloudfront_access" {
  count  = var.create_s3_bucket_policy ? 1 : 0
  bucket = var.s3_bucket_id
  policy = data.aws_iam_policy_document.s3_policy.json
}
