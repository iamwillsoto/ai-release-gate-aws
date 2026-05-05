resource "aws_dynamodb_table" "results" {
  name         = "${local.name_prefix}-results"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "test_id"
  range_key = "execution_timestamp"

  attribute {
    name = "test_id"
    type = "S"
  }

  attribute {
    name = "execution_timestamp"
    type = "S"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-results"
  })
}