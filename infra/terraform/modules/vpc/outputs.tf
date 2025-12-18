# VPC Module Outputs

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "ID of the private subnet"
  value       = aws_subnet.private.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs (for ECS compatibility)"
  value       = [aws_subnet.private.id]
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = aws_nat_gateway.main.id
}

output "nat_gateway_public_ip" {
  description = "Public IP of the NAT Gateway"
  value       = aws_eip.nat.public_ip
}

output "vpc_endpoints_security_group_id" {
  description = "Security group ID for VPC endpoints"
  value       = aws_security_group.vpc_endpoints.id
}

output "s3_endpoint_id" {
  description = "ID of the S3 VPC endpoint"
  value       = aws_vpc_endpoint.s3.id
}

output "dynamodb_endpoint_id" {
  description = "ID of the DynamoDB VPC endpoint"
  value       = aws_vpc_endpoint.dynamodb.id
}

output "ecr_api_endpoint_id" {
  description = "ID of the ECR API VPC endpoint"
  value       = aws_vpc_endpoint.ecr_api.id
}

output "ecr_dkr_endpoint_id" {
  description = "ID of the ECR DKR VPC endpoint"
  value       = aws_vpc_endpoint.ecr_dkr.id
}

output "logs_endpoint_id" {
  description = "ID of the CloudWatch Logs VPC endpoint"
  value       = aws_vpc_endpoint.logs.id
}

output "secretsmanager_endpoint_id" {
  description = "ID of the Secrets Manager VPC endpoint"
  value       = aws_vpc_endpoint.secretsmanager.id
}

output "sts_endpoint_id" {
  description = "ID of the STS VPC endpoint"
  value       = aws_vpc_endpoint.sts.id
}

# VPC Flow Logs Outputs
output "flow_log_id" {
  description = "ID of the VPC Flow Log"
  value       = length(aws_flow_log.main) > 0 ? aws_flow_log.main[0].id : null
}

output "flow_log_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for VPC Flow Logs"
  value       = length(aws_cloudwatch_log_group.vpc_flow_logs) > 0 ? aws_cloudwatch_log_group.vpc_flow_logs[0].arn : null
}

# Security Services Outputs
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = length(aws_guardduty_detector.main) > 0 ? aws_guardduty_detector.main[0].id : null
}

output "inspector_enabled" {
  description = "Whether AWS Inspector is enabled"
  value       = var.enable_inspector
}

output "config_bucket_id" {
  description = "ID of the AWS Config S3 bucket"
  value       = length(aws_s3_bucket.config) > 0 ? aws_s3_bucket.config[0].id : null
}

output "config_recorder_id" {
  description = "ID of the AWS Config recorder"
  value       = length(aws_config_configuration_recorder.main) > 0 ? aws_config_configuration_recorder.main[0].id : null
}
