# CloudWatch Alarms Module - Observability
# Requirements: 11.3 - Step Functions execution failed alarm
# Requirements: 11.4 - ECS task failed alarm
# Requirements: 11.5 - API 5xx error rate alarm

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# SNS Topic for Alarm Notifications
# =============================================================================

resource "aws_sns_topic" "alarms" {
  name = "${local.name_prefix}-alarms"

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-alarms"
  })
}

# =============================================================================
# Step Functions Execution Failed Alarm (Requirements 11.3)
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "sfn_execution_failed" {
  alarm_name          = "${local.name_prefix}-sfn-execution-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.sfn_alarm_evaluation_periods
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = var.sfn_alarm_period
  statistic           = "Sum"
  threshold           = var.sfn_failed_threshold
  alarm_description   = "Step Functions execution failed - repository processing workflow failure"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = var.step_functions_arn
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-sfn-execution-failed"
  })
}

# Additional alarm for Step Functions timeouts
resource "aws_cloudwatch_metric_alarm" "sfn_execution_timed_out" {
  alarm_name          = "${local.name_prefix}-sfn-execution-timed-out"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.sfn_alarm_evaluation_periods
  metric_name         = "ExecutionsTimedOut"
  namespace           = "AWS/States"
  period              = var.sfn_alarm_period
  statistic           = "Sum"
  threshold           = var.sfn_timeout_threshold
  alarm_description   = "Step Functions execution timed out - repository processing exceeded time limit"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = var.step_functions_arn
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-sfn-execution-timed-out"
  })
}


# =============================================================================
# ECS Task Failed Alarm (Requirements 11.4)
# Uses CloudWatch Container Insights metrics if enabled, otherwise ECS service metrics
# =============================================================================

# ECS Task Stopped with non-zero exit code alarm
resource "aws_cloudwatch_metric_alarm" "ecs_task_failed" {
  alarm_name          = "${local.name_prefix}-ecs-task-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.ecs_alarm_evaluation_periods
  threshold           = var.ecs_failed_threshold
  alarm_description   = "ECS Fargate task failed - processor container exited with error"
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "failed_tasks"
    expression  = "FILL(m1, 0)"
    label       = "Failed Tasks"
    return_data = true
  }

  metric_query {
    id = "m1"
    metric {
      metric_name = "TaskCount"
      namespace   = "ECS/ContainerInsights"
      period      = var.ecs_alarm_period
      stat        = "Sum"

      dimensions = {
        ClusterName          = var.ecs_cluster_name
        TaskDefinitionFamily = var.ecs_task_family
      }
    }
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-ecs-task-failed"
  })
}

# Alternative: Monitor ECS task stopped events via CloudWatch Logs metric filter
resource "aws_cloudwatch_log_metric_filter" "ecs_task_stopped" {
  count = var.enable_log_metric_filters ? 1 : 0

  name           = "${local.name_prefix}-ecs-task-stopped"
  pattern        = "{ $.detail.lastStatus = \"STOPPED\" && $.detail.stoppedReason = \"*error*\" }"
  log_group_name = var.ecs_log_group_name

  metric_transformation {
    name          = "ECSTaskStoppedWithError"
    namespace     = "${var.project}/${var.environment}"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_task_stopped_error" {
  count = var.enable_log_metric_filters ? 1 : 0

  alarm_name          = "${local.name_prefix}-ecs-task-stopped-error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.ecs_alarm_evaluation_periods
  metric_name         = "ECSTaskStoppedWithError"
  namespace           = "${var.project}/${var.environment}"
  period              = var.ecs_alarm_period
  statistic           = "Sum"
  threshold           = var.ecs_failed_threshold
  alarm_description   = "ECS task stopped with error - check processor logs"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-ecs-task-stopped-error"
  })
}

# =============================================================================
# API Gateway 5xx Error Rate Alarm (Requirements 11.5)
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${local.name_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.api_alarm_evaluation_periods
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = var.api_alarm_period
  statistic           = "Sum"
  threshold           = var.api_5xx_threshold
  alarm_description   = "API Gateway 5xx error rate spike - server errors detected"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = var.api_gateway_name
    Stage   = var.api_gateway_stage
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-5xx-errors"
  })
}

# API Gateway 5xx Error Rate (percentage) alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx_error_rate" {
  alarm_name          = "${local.name_prefix}-api-5xx-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.api_alarm_evaluation_periods
  threshold           = var.api_5xx_rate_threshold
  alarm_description   = "API Gateway 5xx error rate exceeded threshold percentage"
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "IF(requests > 0, (errors / requests) * 100, 0)"
    label       = "5xx Error Rate (%)"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "5XXError"
      namespace   = "AWS/ApiGateway"
      period      = var.api_alarm_period
      stat        = "Sum"

      dimensions = {
        ApiName = var.api_gateway_name
        Stage   = var.api_gateway_stage
      }
    }
  }

  metric_query {
    id = "requests"
    metric {
      metric_name = "Count"
      namespace   = "AWS/ApiGateway"
      period      = var.api_alarm_period
      stat        = "Sum"

      dimensions = {
        ApiName = var.api_gateway_name
        Stage   = var.api_gateway_stage
      }
    }
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-5xx-error-rate"
  })
}

# API Gateway 4xx Error Rate alarm (optional, for monitoring client errors)
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  count = var.enable_4xx_alarm ? 1 : 0

  alarm_name          = "${local.name_prefix}-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.api_alarm_evaluation_periods
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = var.api_alarm_period
  statistic           = "Sum"
  threshold           = var.api_4xx_threshold
  alarm_description   = "API Gateway 4xx error rate spike - client errors detected"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = var.api_gateway_name
    Stage   = var.api_gateway_stage
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-4xx-errors"
  })
}

# API Gateway Latency alarm
resource "aws_cloudwatch_metric_alarm" "api_latency" {
  count = var.enable_latency_alarm ? 1 : 0

  alarm_name          = "${local.name_prefix}-api-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = var.api_alarm_evaluation_periods
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = var.api_alarm_period
  extended_statistic  = "p95"
  threshold           = var.api_latency_threshold
  alarm_description   = "API Gateway p95 latency exceeded threshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiName = var.api_gateway_name
    Stage   = var.api_gateway_stage
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-high-latency"
  })
}
