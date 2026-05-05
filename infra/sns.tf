resource "aws_sns_topic" "blocked_release" {
  name = "${local.name_prefix}-blocked-release-alerts"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-blocked-release-alerts"
  })
}