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
