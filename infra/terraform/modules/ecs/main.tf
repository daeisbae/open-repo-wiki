# ECS Module - Compute Infrastructure
# Requirements: 4.4 - ECS Fargate task with environment variables
# Requirements: 11.1 - CloudWatch Logs for ECS tasks

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# ECS Cluster
# =============================================================================

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = var.enable_container_insights ? "enabled" : "disabled"
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-cluster"
  })
}

# =============================================================================
# CloudWatch Log Group for ECS Tasks (Requirements 11.1)
# =============================================================================

resource "aws_cloudwatch_log_group" "processor" {
  name              = "/ecs/${local.name_prefix}-processor"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-processor-logs"
  })
}

# =============================================================================
# Security Group for ECS Tasks
# =============================================================================

resource "aws_security_group" "ecs_tasks" {
  name        = "${local.name_prefix}-ecs-tasks-sg"
  description = "Security group for ECS Fargate tasks"
  vpc_id      = var.vpc_id

  # Allow all outbound traffic (for GitHub API, LLM providers)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-ecs-tasks-sg"
  })
}

# =============================================================================
# ECS Task Definition (Requirements 4.4)
# Fargate task with environment variables for processor
# =============================================================================

resource "aws_ecs_task_definition" "processor" {
  family                   = "${local.name_prefix}-processor"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  # ARM64 (Graviton) for better price/performance
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = var.cpu_architecture
  }

  container_definitions = jsonencode([
    {
      name      = "processor"
      image     = "${var.ecr_repository_url}:${var.processor_image_tag}"
      essential = true

      # Environment variables (Requirements 4.4)
      environment = [
        {
          name  = "DDB_MAIN_TABLE"
          value = var.dynamodb_main_table_name
        },
        {
          name  = "DDB_JOBS_TABLE"
          value = var.dynamodb_jobs_table_name
        },
        {
          name  = "S3_BUCKET"
          value = var.s3_artifacts_bucket_name
        },
        {
          name  = "MAX_FILES_FOR_FULL_SUMMARY"
          value = tostring(var.max_files_for_full_summary)
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "LLM_PROVIDER"
          value = var.llm_provider
        },
        {
          name  = "LLM_MODELNAME"
          value = var.llm_model_name
        }
      ]

      # Secrets from Secrets Manager (injected at runtime)
      secrets = var.secrets_config

      # CloudWatch Logs configuration (Requirements 11.1)
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.processor.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "processor"
        }
      }

      # Health check (optional)
      healthCheck = var.enable_health_check ? {
        command     = ["CMD-SHELL", "exit 0"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      } : null
    }
  ])

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-processor"
  })
}

# =============================================================================
# ECS Cluster Capacity Providers
# =============================================================================

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = var.use_fargate_spot ? "FARGATE_SPOT" : "FARGATE"
  }
}
