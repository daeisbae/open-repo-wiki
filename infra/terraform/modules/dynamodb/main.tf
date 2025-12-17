# DynamoDB Module - Data Storage
# Requirements: 2.1, 2.5 - Main table and Jobs table with PK/SK

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# OpenRepoWikiMain Table (Requirements 2.1, 2.2, 2.3, 2.4)
# Stores: Repositories, Branches, Tree Nodes
# =============================================================================

resource "aws_dynamodb_table" "main" {
  name         = "${local.name_prefix}-main"
  billing_mode = "PAY_PER_REQUEST" # On-demand capacity

  # Primary key: PK (partition key) + SK (sort key)
  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Enable server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-main"
  })
}

# =============================================================================
# OpenRepoWikiJobs Table (Requirements 2.5, 2.6)
# Stores: Job status and progress
# =============================================================================

resource "aws_dynamodb_table" "jobs" {
  name         = "${local.name_prefix}-jobs"
  billing_mode = "PAY_PER_REQUEST" # On-demand capacity

  # Primary key: PK (partition key) + SK (sort key)
  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # GSI for querying jobs by status (for concurrency limit check)
  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "status"
    projection_type = "ALL"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  # Enable server-side encryption
  server_side_encryption {
    enabled = true
  }

  # TTL for automatic cleanup of old jobs
  ttl {
    attribute_name = "ttl"
    enabled        = var.enable_jobs_ttl
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-jobs"
  })
}
