# API Gateway Module - REST API for OpenRepoWiki
# Requirements: 4.1, 6.3, 7.1, 7.3 - Job creation, progress tracking, tree and page retrieval

locals {
  name_prefix = "${var.project}-${var.environment}"
}

# =============================================================================
# REST API Definition
# =============================================================================

resource "aws_api_gateway_rest_api" "main" {
  name        = "${local.name_prefix}-api"
  description = "OpenRepoWiki REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api"
  })
}

# =============================================================================
# Request Authorizer (Lambda)
# Validates HMAC-signed requests for protected endpoints
# =============================================================================

resource "aws_api_gateway_authorizer" "request_authorizer" {
  count                            = var.enable_request_authorizer ? 1 : 0
  name                             = "${local.name_prefix}-request-authorizer"
  rest_api_id                      = aws_api_gateway_rest_api.main.id
  authorizer_uri                   = var.authorizer_invoke_arn
  authorizer_credentials           = var.authorizer_credentials_arn
  type                             = "REQUEST"
  identity_source                  = "method.request.header.X-Timestamp,method.request.header.X-Signature"
  authorizer_result_ttl_in_seconds = var.authorizer_cache_ttl
}


# =============================================================================
# /jobs Resource - POST /jobs, GET /jobs/{jobId}
# Requirements: 4.1 - Job creation with PENDING status
# Requirements: 6.3 - Job status retrieval
# =============================================================================

resource "aws_api_gateway_resource" "jobs" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "jobs"
}

# POST /jobs - Create new job
resource "aws_api_gateway_method" "jobs_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.jobs.id
  http_method   = "POST"
  authorization = var.enable_request_authorizer ? "CUSTOM" : "NONE"
  authorizer_id = var.enable_request_authorizer ? aws_api_gateway_authorizer.request_authorizer[0].id : null
}

resource "aws_api_gateway_integration" "jobs_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.jobs.id
  http_method             = aws_api_gateway_method.jobs_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.jobs_handler_invoke_arn
}


# /jobs/{jobId} Resource
resource "aws_api_gateway_resource" "jobs_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.jobs.id
  path_part   = "{jobId}"
}

# GET /jobs/{jobId} - Get job status
resource "aws_api_gateway_method" "jobs_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.jobs_id.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.jobId" = true
  }
}

resource "aws_api_gateway_integration" "jobs_id_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.jobs_id.id
  http_method             = aws_api_gateway_method.jobs_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.jobs_handler_invoke_arn
}

# =============================================================================
# /repos Resource - GET /repos/{repoId}/tree, GET /repos/{repoId}/page
# Requirements: 7.1 - Tree retrieval from DynamoDB
# Requirements: 7.3 - Page content retrieval
# =============================================================================

resource "aws_api_gateway_resource" "repos" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "repos"
}

# /repos/{owner}
resource "aws_api_gateway_resource" "repos_owner" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.repos.id
  path_part   = "{owner}"
}

# /repos/{owner}/{name}
resource "aws_api_gateway_resource" "repos_name" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.repos_owner.id
  path_part   = "{name}"
}

# /repos/{owner}/{name}/tree
resource "aws_api_gateway_resource" "repos_tree" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.repos_name.id
  path_part   = "tree"
}

# GET /repos/{owner}/{name}/tree
resource "aws_api_gateway_method" "repos_tree_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.repos_tree.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.owner"         = true
    "method.request.path.name"          = true
    "method.request.querystring.branch" = false
    "method.request.querystring.path"   = false
  }
}

resource "aws_api_gateway_integration" "repos_tree_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.repos_tree.id
  http_method             = aws_api_gateway_method.repos_tree_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.repos_handler_invoke_arn
}

# /repos/{owner}/{name}/page
resource "aws_api_gateway_resource" "repos_page" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.repos_name.id
  path_part   = "page"
}

# GET /repos/{owner}/{name}/page
resource "aws_api_gateway_method" "repos_page_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.repos_page.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.owner"         = true
    "method.request.path.name"          = true
    "method.request.querystring.branch" = false
    "method.request.querystring.path"   = false
  }
}

resource "aws_api_gateway_integration" "repos_page_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.repos_page.id
  http_method             = aws_api_gateway_method.repos_page_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.repos_handler_invoke_arn
}

# =============================================================================
# CORS Configuration
# =============================================================================

# OPTIONS for /jobs
resource "aws_api_gateway_method" "jobs_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.jobs.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "jobs_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.jobs.id
  http_method = aws_api_gateway_method.jobs_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "jobs_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.jobs.id
  http_method = aws_api_gateway_method.jobs_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "jobs_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.jobs.id
  http_method = aws_api_gateway_method.jobs_options.http_method
  status_code = aws_api_gateway_method_response.jobs_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS for /jobs/{jobId}
resource "aws_api_gateway_method" "jobs_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.jobs_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "jobs_id_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.jobs_id.id
  http_method = aws_api_gateway_method.jobs_id_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "jobs_id_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.jobs_id.id
  http_method = aws_api_gateway_method.jobs_id_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "jobs_id_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.jobs_id.id
  http_method = aws_api_gateway_method.jobs_id_options.http_method
  status_code = aws_api_gateway_method_response.jobs_id_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}


# OPTIONS for /repos/{repoId}/tree
resource "aws_api_gateway_method" "repos_tree_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.repos_tree.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "repos_tree_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.repos_tree.id
  http_method = aws_api_gateway_method.repos_tree_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "repos_tree_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.repos_tree.id
  http_method = aws_api_gateway_method.repos_tree_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "repos_tree_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.repos_tree.id
  http_method = aws_api_gateway_method.repos_tree_options.http_method
  status_code = aws_api_gateway_method_response.repos_tree_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS for /repos/{repoId}/page
resource "aws_api_gateway_method" "repos_page_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.repos_page.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "repos_page_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.repos_page.id
  http_method = aws_api_gateway_method.repos_page_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "repos_page_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.repos_page.id
  http_method = aws_api_gateway_method.repos_page_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "repos_page_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.repos_page.id
  http_method = aws_api_gateway_method.repos_page_options.http_method
  status_code = aws_api_gateway_method_response.repos_page_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# =============================================================================
# API Deployment and Stage
# =============================================================================

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.jobs.id,
      aws_api_gateway_resource.jobs_id.id,
      aws_api_gateway_resource.repos.id,
      aws_api_gateway_resource.repos_owner.id,
      aws_api_gateway_resource.repos_name.id,
      aws_api_gateway_resource.repos_tree.id,
      aws_api_gateway_resource.repos_page.id,
      aws_api_gateway_method.jobs_post.id,
      aws_api_gateway_method.jobs_id_get.id,
      aws_api_gateway_method.repos_tree_get.id,
      aws_api_gateway_method.repos_page_get.id,
      aws_api_gateway_integration.jobs_post.id,
      aws_api_gateway_integration.jobs_id_get.id,
      aws_api_gateway_integration.repos_tree_get.id,
      aws_api_gateway_integration.repos_page_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.jobs_post,
    aws_api_gateway_integration.jobs_id_get,
    aws_api_gateway_integration.repos_tree_get,
    aws_api_gateway_integration.repos_page_get,
    aws_api_gateway_integration.jobs_options,
    aws_api_gateway_integration.jobs_id_options,
    aws_api_gateway_integration.repos_tree_options,
    aws_api_gateway_integration.repos_page_options,
  ]
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name

  # Access logs (separate from execution logs, doesn't require account-level role)
  dynamic "access_log_settings" {
    for_each = var.enable_access_logs ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_access_logs[0].arn
      format = jsonencode({
        requestId        = "$context.requestId"
        ip               = "$context.identity.sourceIp"
        caller           = "$context.identity.caller"
        user             = "$context.identity.user"
        requestTime      = "$context.requestTime"
        httpMethod       = "$context.httpMethod"
        resourcePath     = "$context.resourcePath"
        status           = "$context.status"
        protocol         = "$context.protocol"
        responseLength   = "$context.responseLength"
        integrationError = "$context.integrationErrorMessage"
      })
    }
  }

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-${var.stage_name}"
  })
}

# =============================================================================
# Gateway Responses (CORS for 4xx/5xx errors)
# Requirements: Fixes "Missing Allow Origin" errors on backend timeout/failure
# =============================================================================

resource "aws_api_gateway_gateway_response" "default_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
  }
}

resource "aws_api_gateway_gateway_response" "default_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'*'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'"
  }
}


# =============================================================================
# CloudWatch Log Group for API Access Logs
# =============================================================================

resource "aws_cloudwatch_log_group" "api_access_logs" {
  count             = var.enable_access_logs ? 1 : 0
  name              = "/aws/apigateway/${local.name_prefix}-api"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-api-logs"
  })
}

# =============================================================================
# API Gateway Account Settings (for CloudWatch Logs)
# =============================================================================

resource "aws_api_gateway_account" "main" {
  count               = var.create_api_gateway_account ? 1 : 0
  cloudwatch_role_arn = var.api_gateway_cloudwatch_role_arn
}

# =============================================================================
# Method Settings (throttling, logging)
# Note: metrics_enabled and logging_level require account-level CloudWatch role
# =============================================================================

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    # Metrics and execution logging require account-level CloudWatch role
    # Set to false/OFF to avoid the requirement
    metrics_enabled        = var.logging_level != "OFF"
    logging_level          = var.logging_level
    data_trace_enabled     = var.data_trace_enabled
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
  }
}
