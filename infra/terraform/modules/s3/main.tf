# S3 Module - Artifact Storage
# Requirements: 3.1, 3.4 - Artifacts bucket with Block Public Access and SSE-S3

locals {
  name_prefix = "${var.project}-${var.environment}"
  bucket_name = lower("${var.project}-artifacts-${var.environment}")
}

# =============================================================================
# S3 Bucket (Requirements 3.1)
# =============================================================================

resource "aws_s3_bucket" "artifacts" {
  bucket = local.bucket_name

  tags = merge(var.tags, {
    Name = local.bucket_name
  })
}

# =============================================================================
# Block Public Access (Requirements 3.1)
# =============================================================================

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# =============================================================================
# Server-Side Encryption with SSE-S3 (Requirements 3.4)
# =============================================================================

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# =============================================================================
# Versioning (for data protection)
# =============================================================================

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

# =============================================================================
# Lifecycle Rules (optional cleanup of old versions)
# =============================================================================

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  count  = var.enable_lifecycle_rules ? 1 : 0
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "cleanup-old-versions"
    status = "Enabled"

    filter {
      prefix = ""  # Apply to all objects
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }
}

# =============================================================================
# Bucket Policy for CloudFront OAC (Requirements 3.5)
# =============================================================================

resource "aws_s3_bucket_policy" "artifacts" {
  count  = var.cloudfront_distribution_arn != "" ? 1 : 0
  bucket = aws_s3_bucket.artifacts.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.artifacts.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = var.cloudfront_distribution_arn
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.artifacts]
}
