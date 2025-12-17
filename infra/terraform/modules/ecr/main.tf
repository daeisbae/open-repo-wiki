# ECR Module - Container Registry
# Requirements: Phase 1 infrastructure - Repository for processor container image

locals {
  name_prefix = lower("${var.project}-${var.environment}")
}

# =============================================================================
# ECR Repository for Processor
# =============================================================================

resource "aws_ecr_repository" "processor" {
  name                 = "${local.name_prefix}-processor"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_arn != "" ? var.kms_key_arn : null
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-processor"
  })
}

# =============================================================================
# Lifecycle Policy (cleanup old images)
# =============================================================================

resource "aws_ecr_lifecycle_policy" "processor" {
  repository = aws_ecr_repository.processor.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.max_image_count} images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# =============================================================================
# Repository Policy (optional - for cross-account access)
# =============================================================================

resource "aws_ecr_repository_policy" "processor" {
  count      = length(var.allowed_account_ids) > 0 ? 1 : 0
  repository = aws_ecr_repository.processor.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCrossAccountPull"
        Effect = "Allow"
        Principal = {
          AWS = [for account_id in var.allowed_account_ids : "arn:aws:iam::${account_id}:root"]
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  })
}
