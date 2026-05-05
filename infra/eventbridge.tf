resource "aws_cloudwatch_event_rule" "s3_contract_upload" {
  name        = "${local.name_prefix}-s3-contract-upload"
  description = "Starts the AI Release Gate workflow when a contract JSON file is uploaded to the input S3 bucket."

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [aws_s3_bucket.input.bucket]
      }
      object = {
        key = [
          {
            prefix = "contracts/"
          }
        ]
      }
    }
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "start_release_gate" {
  rule      = aws_cloudwatch_event_rule.s3_contract_upload.name
  target_id = "StartAIReleaseGateStateMachine"
  arn       = aws_sfn_state_machine.release_gate.arn
  role_arn  = aws_iam_role.eventbridge_exec.arn
}