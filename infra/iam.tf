resource "aws_iam_role" "lambda_exec" {
  name = "${local.name_prefix}-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "lambda_data_access" {
  name        = "${local.name_prefix}-lambda-data-access"
  description = "Allows AI Release Gate Lambda functions to access S3 artifacts and DynamoDB results."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowInputBucketRead"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.input.arn,
          "${aws_s3_bucket.input.arn}/*"
        ]
      },
      {
        Sid    = "AllowArtifactBucketWrite"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      {
        Sid    = "AllowDynamoDBWrites"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.results.arn
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_data_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_data_access.arn
}

resource "aws_iam_role" "step_functions_exec" {
  name = "${local.name_prefix}-step-functions-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "step_functions_lambda_invoke" {
  name        = "${local.name_prefix}-step-functions-lambda-invoke"
  description = "Allows Step Functions to invoke AI Release Gate Lambda functions."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowInvokeReleaseGateLambdas"
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.validate_contract.arn,
          aws_lambda_function.invoke_bedrock.arn,
          aws_lambda_function.evaluate_response.arn,
          aws_lambda_function.write_results.arn
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "step_functions_lambda_invoke" {
  role       = aws_iam_role.step_functions_exec.name
  policy_arn = aws_iam_policy.step_functions_lambda_invoke.arn
}

resource "aws_iam_role" "eventbridge_exec" {
  name = "${local.name_prefix}-eventbridge-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "eventbridge_start_stepfunctions" {
  name        = "${local.name_prefix}-eventbridge-start-stepfunctions"
  description = "Allows EventBridge to start the AI Release Gate Step Functions workflow."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowStartReleaseGateStateMachine"
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.release_gate.arn
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "eventbridge_start_stepfunctions" {
  role       = aws_iam_role.eventbridge_exec.name
  policy_arn = aws_iam_policy.eventbridge_start_stepfunctions.arn
}

resource "aws_iam_policy" "step_functions_sns_publish" {
  name        = "${local.name_prefix}-step-functions-sns-publish"
  description = "Allows Step Functions to publish blocked AI release alerts to SNS."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowPublishBlockedReleaseAlerts"
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.blocked_release.arn
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "step_functions_sns_publish" {
  role       = aws_iam_role.step_functions_exec.name
  policy_arn = aws_iam_policy.step_functions_sns_publish.arn
}
