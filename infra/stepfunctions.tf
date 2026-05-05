resource "aws_sfn_state_machine" "release_gate" {
  name     = "${local.name_prefix}-state-machine"
  role_arn = aws_iam_role.step_functions_exec.arn

  definition = jsonencode({
    Comment = "AI Release Gate workflow for contract validation, model invocation, response evaluation, result persistence, and blocked-release notification."
    StartAt = "ValidateContract"

    States = {
      ValidateContract = {
        Type     = "Task"
        Resource = aws_lambda_function.validate_contract.arn
        Next     = "CheckContractValidity"
      }

      CheckContractValidity = {
        Type = "Choice"
        Choices = [
          {
            Variable      = "$.contract_valid"
            BooleanEquals = true
            Next          = "InvokeModel"
          }
        ]
        Default = "ContractInvalid"
      }

      ContractInvalid = {
        Type  = "Fail"
        Error = "InvalidContract"
        Cause = "The submitted AI release gate contract failed validation."
      }

      InvokeModel = {
        Type     = "Task"
        Resource = aws_lambda_function.invoke_bedrock.arn
        Next     = "EvaluateResponse"
      }

      EvaluateResponse = {
        Type     = "Task"
        Resource = aws_lambda_function.evaluate_response.arn
        Next     = "WriteResults"
      }

      WriteResults = {
        Type     = "Task"
        Resource = aws_lambda_function.write_results.arn
        Next     = "ReleaseDecision"
      }

      ReleaseDecision = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.release_decision"
            StringEquals = "APPROVED"
            Next         = "Approved"
          },
          {
            Variable     = "$.release_decision"
            StringEquals = "BLOCKED"
            Next         = "PublishBlockedReleaseAlert"
          },
          {
            Variable     = "$.release_decision"
            StringEquals = "REVIEW"
            Next         = "ReviewRequired"
          }
        ]
        Default = "ReviewRequired"
      }

      PublishBlockedReleaseAlert = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn    = aws_sns_topic.blocked_release.arn
          Subject     = "AI Release Gate BLOCKED"
          "Message.$" = "States.Format('AI Release Gate blocked a release. Test ID: {} | Test Name: {} | Severity: {} | Status: {} | Artifact: s3://{}/{}', $.test_id, $.test_name, $.severity, $.evaluation_status, $.artifact_bucket, $.artifact_key)"
        }
        Next = "Blocked"
      }

      Approved = {
        Type = "Succeed"
      }

      Blocked = {
        Type = "Succeed"
      }

      ReviewRequired = {
        Type = "Succeed"
      }
    }
  })

  tags = local.common_tags
}
