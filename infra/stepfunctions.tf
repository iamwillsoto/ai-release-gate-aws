resource "aws_sfn_state_machine" "release_gate" {
  name     = "${local.name_prefix}-state-machine"
  role_arn = aws_iam_role.step_functions_exec.arn

  definition = jsonencode({
    Comment = "AI Release Gate workflow for contract validation, model invocation, response evaluation, and result formatting."
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
            Next         = "Blocked"
          },
          {
            Variable     = "$.release_decision"
            StringEquals = "REVIEW"
            Next         = "ReviewRequired"
          }
        ]
        Default = "ReviewRequired"
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