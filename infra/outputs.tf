output "input_bucket_name" {
  description = "S3 bucket for AI release gate input contracts."
  value       = aws_s3_bucket.input.bucket
}

output "artifact_bucket_name" {
  description = "S3 bucket for AI release gate audit artifacts."
  value       = aws_s3_bucket.artifacts.bucket
}

output "results_table_name" {
  description = "DynamoDB table for release gate results."
  value       = aws_dynamodb_table.results.name
}

output "validate_contract_lambda_name" {
  description = "Lambda function that validates AI release gate contracts."
  value       = aws_lambda_function.validate_contract.function_name
}

output "invoke_bedrock_lambda_name" {
  description = "Lambda function that invokes the model or mock model."
  value       = aws_lambda_function.invoke_bedrock.function_name
}

output "evaluate_response_lambda_name" {
  description = "Lambda function that evaluates model responses."
  value       = aws_lambda_function.evaluate_response.function_name
}

output "write_results_lambda_name" {
  description = "Lambda function that formats and writes release gate results."
  value       = aws_lambda_function.write_results.function_name
}

output "step_functions_state_machine_name" {
  description = "Step Functions workflow for the AI Release Gate."
  value       = aws_sfn_state_machine.release_gate.name
}

output "step_functions_state_machine_arn" {
  description = "ARN of the AI Release Gate Step Functions workflow."
  value       = aws_sfn_state_machine.release_gate.arn
}

output "eventbridge_rule_name" {
  description = "EventBridge rule that starts the AI Release Gate from S3 contract uploads."
  value       = aws_cloudwatch_event_rule.s3_contract_upload.name
}

output "blocked_release_sns_topic_name" {
  description = "SNS topic used for blocked AI release alerts."
  value       = aws_sns_topic.blocked_release.name
}

output "blocked_release_sns_topic_arn" {
  description = "SNS topic ARN used for blocked AI release alerts."
  value       = aws_sns_topic.blocked_release.arn
}