# Lambda Module - API Handlers
# Requirements: 11.2 - CloudWatch Logs for API requests

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# Placeholder Lambda Code (for initial deployment)
# =============================================================================

data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    content  = <<-EOF
      def handler(event, context):
          return {
              'statusCode': 200,
              'body': 'Placeholder - deploy actual code'
          }
    EOF
    filename = "handler.py"
  }
}

# =============================================================================
# CloudWatch Log Groups for Lambda Functions (Requirements 11.2)
# =============================================================================

resource "aws_cloudwatch_log_group" "jobs_handler" {
  name              = "/aws/lambda/${local.name_prefix}-jobs-handler"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-jobs-handler-logs"
  })
}

resource "aws_cloudwatch_log_group" "repos_handler" {
  name              = "/aws/lambda/${local.name_prefix}-repos-handler"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-repos-handler-logs"
  })
}

# =============================================================================
# Lambda Function: Jobs Handler
# Handles POST /jobs and GET /jobs/{jobId}
# =============================================================================

resource "aws_lambda_function" "jobs_handler" {
  function_name = "${local.name_prefix}-jobs-handler"
  description   = "Handles job creation and status retrieval"
  role          = var.lambda_execution_role_arn
  handler       = var.jobs_handler_handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size

  # Use placeholder for initial deployment, actual code deployed separately
  filename         = var.jobs_handler_package_path != "" ? var.jobs_handler_package_path : data.archive_file.placeholder.output_path
  source_code_hash = var.jobs_handler_package_path != "" ? var.jobs_handler_source_hash : data.archive_file.placeholder.output_base64sha256

  environment {
    variables = merge({
      DDB_MAIN_TABLE      = var.dynamodb_main_table_name
      DDB_JOBS_TABLE      = var.dynamodb_jobs_table_name
      S3_BUCKET           = var.s3_artifacts_bucket_name
      STATE_MACHINE_ARN   = var.step_functions_arn
      MAX_CONCURRENT_JOBS = tostring(var.max_concurrent_jobs)
      LOG_LEVEL           = var.lambda_log_level
    }, var.additional_env_vars)
  }

  # Ensure log group exists before function
  depends_on = [aws_cloudwatch_log_group.jobs_handler]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-jobs-handler"
  })
}

# =============================================================================
# Lambda Function: Repos Handler
# Handles GET /repos/{repoId}/tree and GET /repos/{repoId}/page
# =============================================================================

resource "aws_lambda_function" "repos_handler" {
  function_name = "${local.name_prefix}-repos-handler"
  description   = "Handles tree and page retrieval"
  role          = var.lambda_execution_role_arn
  handler       = var.repos_handler_handler
  runtime       = var.runtime
  timeout       = var.timeout
  memory_size   = var.memory_size

  # Use placeholder for initial deployment, actual code deployed separately
  filename         = var.repos_handler_package_path != "" ? var.repos_handler_package_path : data.archive_file.placeholder.output_path
  source_code_hash = var.repos_handler_package_path != "" ? var.repos_handler_source_hash : data.archive_file.placeholder.output_base64sha256

  environment {
    variables = merge({
      DDB_MAIN_TABLE = var.dynamodb_main_table_name
      DDB_JOBS_TABLE = var.dynamodb_jobs_table_name
      S3_BUCKET      = var.s3_artifacts_bucket_name
      LOG_LEVEL      = var.lambda_log_level
    }, var.additional_env_vars)
  }

  # Ensure log group exists before function
  depends_on = [aws_cloudwatch_log_group.repos_handler]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-repos-handler"
  })
}

# =============================================================================
# Lambda Permissions for API Gateway (to be used by API Gateway module)
# =============================================================================

resource "aws_lambda_permission" "jobs_handler_apigw" {
  count         = var.create_api_gateway_permissions ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.jobs_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

resource "aws_lambda_permission" "repos_handler_apigw" {
  count         = var.create_api_gateway_permissions ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.repos_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}

# =============================================================================
# Lambda Function: Request Authorizer
# Validates HMAC-signed requests for protected endpoints
# =============================================================================

resource "aws_cloudwatch_log_group" "authorizer" {
  count             = var.enable_authorizer ? 1 : 0
  name              = "/aws/lambda/${local.name_prefix}-authorizer"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-authorizer-logs"
  })
}

resource "aws_lambda_function" "authorizer" {
  count         = var.enable_authorizer ? 1 : 0
  function_name = "${local.name_prefix}-authorizer"
  description   = "Request authorizer for protected API endpoints"
  role          = var.authorizer_execution_role_arn != "" ? var.authorizer_execution_role_arn : var.lambda_execution_role_arn
  handler       = var.authorizer_handler
  runtime       = var.runtime
  timeout       = 10  # Authorizers should be fast
  memory_size   = 128

  # Use placeholder for initial deployment, actual code deployed separately
  filename         = var.authorizer_package_path != "" ? var.authorizer_package_path : data.archive_file.placeholder.output_path
  source_code_hash = var.authorizer_package_path != "" ? var.authorizer_source_hash : data.archive_file.placeholder.output_base64sha256

  environment {
    variables = merge({
      SIGNING_SECRET_ARN = var.authorizer_secret_arn
      LOG_LEVEL          = var.lambda_log_level
    }, var.additional_env_vars)
  }

  # Ensure log group exists before function
  depends_on = [aws_cloudwatch_log_group.authorizer]

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-authorizer"
  })
}

resource "aws_lambda_permission" "authorizer_apigw" {
  count         = var.enable_authorizer && var.create_api_gateway_permissions ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/authorizers/*"
}

