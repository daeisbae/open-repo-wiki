# Step Functions Module - Workflow Orchestration
# Requirements: 4.2 - Start Step Functions execution to orchestrate processing
# Requirements: 4.3 - Launch ECS Fargate task with callback pattern

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# CloudWatch Log Group for Step Functions
# =============================================================================

resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/states/${local.name_prefix}-processor"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-sfn-logs"
  })
}

# =============================================================================
# IAM Role for Step Functions
# =============================================================================

resource "aws_iam_role" "sfn_execution" {
  name = "${local.name_prefix}-sfn-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Allow Step Functions to run ECS tasks
resource "aws_iam_role_policy" "sfn_ecs" {
  name = "${local.name_prefix}-sfn-ecs"
  role = aws_iam_role.sfn_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:DescribeTasks"
        ]
        Resource = "*"
        Condition = {
          ArnEquals = {
            "ecs:cluster" = var.ecs_cluster_arn
          }
        }
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          var.ecs_task_execution_role_arn,
          var.ecs_task_role_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "events:PutTargets",
          "events:PutRule",
          "events:DescribeRule"
        ]
        Resource = "arn:aws:events:${var.aws_region}:*:rule/StepFunctionsGetEventsForECSTaskRule"
      }
    ]
  })
}

# Allow Step Functions to write logs
resource "aws_iam_role_policy" "sfn_logs" {
  name = "${local.name_prefix}-sfn-logs"
  role = aws_iam_role.sfn_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutLogEvents",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# =============================================================================
# Step Functions State Machine (Requirements 4.2, 4.3)
# Uses callback pattern for ECS task integration
# =============================================================================

resource "aws_sfn_state_machine" "processor" {
  name     = "${local.name_prefix}-processor"
  role_arn = aws_iam_role.sfn_execution.arn

  definition = jsonencode({
    Comment = "OpenRepoWiki Repository Processing Workflow"
    StartAt = "RunProcessorTask"
    States = {
      RunProcessorTask = {
        Type     = "Task"
        Resource = "arn:aws:states:::ecs:runTask.waitForTaskToken"
        Parameters = {
          LaunchType     = "FARGATE"
          Cluster        = var.ecs_cluster_arn
          TaskDefinition = var.ecs_task_definition_arn
          NetworkConfiguration = {
            AwsvpcConfiguration = {
              Subnets        = var.private_subnet_ids
              SecurityGroups = [var.ecs_security_group_id]
              AssignPublicIp = "DISABLED"
            }
          }
          Overrides = {
            ContainerOverrides = [
              {
                Name = "processor"
                Environment = [
                  {
                    "Name"    = "REPO_OWNER"
                    "Value.$" = "$.repoOwner"
                  },
                  {
                    "Name"    = "REPO_NAME"
                    "Value.$" = "$.repoName"
                  },
                  {
                    "Name"    = "BRANCH"
                    "Value.$" = "$.branch"
                  },
                  {
                    "Name"    = "JOB_ID"
                    "Value.$" = "$.jobId"
                  },
                  {
                    "Name"    = "TASK_TOKEN"
                    "Value.$" = "$$.Task.Token"
                  }
                ]
              }
            ]
          }
        }
        # Retry configuration for transient failures
        Retry = [
          {
            ErrorEquals = [
              "ECS.AmazonECSException",
              "ECS.ServiceException"
            ]
            IntervalSeconds = 30
            MaxAttempts     = 3
            BackoffRate     = 2.0
          }
        ]
        # Catch all errors and transition to failed state
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath  = "$.error"
            Next        = "ProcessingFailed"
          }
        ]
        TimeoutSeconds = var.task_timeout_seconds
        Next           = "ProcessingSucceeded"
      }
      ProcessingSucceeded = {
        Type = "Succeed"
      }
      ProcessingFailed = {
        Type  = "Fail"
        Error = "ProcessingError"
        Cause = "Repository processing failed"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true
    level                  = var.log_level
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-processor"
  })
}
