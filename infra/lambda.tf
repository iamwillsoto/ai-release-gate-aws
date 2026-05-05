data "archive_file" "validate_contract" {
  type        = "zip"
  source_file = "${path.module}/../lambda/validate_contract/app.py"
  output_path = "${path.module}/build/validate_contract.zip"
}

data "archive_file" "invoke_bedrock" {
  type        = "zip"
  source_file = "${path.module}/../lambda/invoke_bedrock/app.py"
  output_path = "${path.module}/build/invoke_bedrock.zip"
}

data "archive_file" "evaluate_response" {
  type        = "zip"
  source_file = "${path.module}/../lambda/evaluate_response/app.py"
  output_path = "${path.module}/build/evaluate_response.zip"
}

data "archive_file" "write_results" {
  type        = "zip"
  source_file = "${path.module}/../lambda/write_results/app.py"
  output_path = "${path.module}/build/write_results.zip"
}

resource "aws_lambda_function" "validate_contract" {
  function_name    = "${local.name_prefix}-validate-contract"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.validate_contract.output_path
  source_code_hash = data.archive_file.validate_contract.output_base64sha256
  timeout          = 10
  memory_size      = 128

  tags = local.common_tags
}

resource "aws_lambda_function" "invoke_bedrock" {
  function_name    = "${local.name_prefix}-invoke-bedrock"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.invoke_bedrock.output_path
  source_code_hash = data.archive_file.invoke_bedrock.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      DEFAULT_MODEL_ID  = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
      USE_MOCK_FALLBACK = "true"
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "evaluate_response" {
  function_name    = "${local.name_prefix}-evaluate-response"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.evaluate_response.output_path
  source_code_hash = data.archive_file.evaluate_response.output_base64sha256
  timeout          = 10
  memory_size      = 128

  tags = local.common_tags
}

resource "aws_lambda_function" "write_results" {
  function_name    = "${local.name_prefix}-write-results"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.write_results.output_path
  source_code_hash = data.archive_file.write_results.output_base64sha256
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      RESULTS_TABLE_NAME = aws_dynamodb_table.results.name
      ARTIFACT_BUCKET    = aws_s3_bucket.artifacts.bucket
      INPUT_BUCKET       = aws_s3_bucket.input.bucket
    }
  }

  tags = local.common_tags
}
