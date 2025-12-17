# Step Functions Module Outputs

output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.processor.arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = aws_sfn_state_machine.processor.name
}

output "state_machine_id" {
  description = "ID of the Step Functions state machine"
  value       = aws_sfn_state_machine.processor.id
}

output "execution_role_arn" {
  description = "ARN of the Step Functions execution role"
  value       = aws_iam_role.sfn_execution.arn
}

output "execution_role_name" {
  description = "Name of the Step Functions execution role"
  value       = aws_iam_role.sfn_execution.name
}

output "log_group_name" {
  description = "CloudWatch Log Group name for Step Functions"
  value       = aws_cloudwatch_log_group.sfn.name
}

output "log_group_arn" {
  description = "CloudWatch Log Group ARN for Step Functions"
  value       = aws_cloudwatch_log_group.sfn.arn
}
