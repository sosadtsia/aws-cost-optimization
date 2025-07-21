# Cost Explorer Lambda function resources

# Create a zip file for Lambda deployment
data "archive_file" "cost_explorer_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/cost_explorer_dashboard.py"
  output_path = "${path.module}/lambda/cost_explorer_dashboard.zip"
}

# IAM role for the Cost Explorer Lambda function
resource "aws_iam_role" "cost_explorer_role" {
  name = "${var.project_name}-cost-explorer-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach policies to the Lambda role
resource "aws_iam_role_policy_attachment" "cost_explorer_basic_execution" {
  role       = aws_iam_role.cost_explorer_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for Cost Explorer and SES access
resource "aws_iam_policy" "cost_explorer_policy" {
  name        = "${var.project_name}-cost-explorer-policy-${var.environment}"
  description = "Policy for cost explorer Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetDimensionValues",
          "ce:GetTags",
          "ses:SendEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cost_explorer_policy_attachment" {
  role       = aws_iam_role.cost_explorer_role.name
  policy_arn = aws_iam_policy.cost_explorer_policy.arn
}

# Lambda function for cost explorer dashboard
resource "aws_lambda_function" "cost_explorer" {
  filename         = data.archive_file.cost_explorer_zip.output_path
  function_name    = "${var.project_name}-cost-explorer-${var.environment}"
  role             = aws_iam_role.cost_explorer_role.arn
  handler          = "cost_explorer_dashboard.lambda_handler"
  source_code_hash = data.archive_file.cost_explorer_zip.output_base64sha256
  runtime          = "python3.9"
  timeout          = 90  # Cost Explorer API calls can take longer
  memory_size      = 256  # Need more memory for processing cost data

  environment {
    variables = {
      SENDER_EMAIL      = var.sender_email
      RECIPIENT_EMAILS  = join(",", var.recipient_emails)
      REPORT_PERIOD_DAYS = var.report_period_days
      BUDGET_THRESHOLD  = var.budget_threshold
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.cost_explorer_basic_execution,
    aws_iam_role_policy_attachment.cost_explorer_policy_attachment
  ]
}

# CloudWatch Event Rule to trigger Lambda on schedule
resource "aws_cloudwatch_event_rule" "cost_explorer_schedule" {
  name                = "${var.project_name}-cost-explorer-schedule-${var.environment}"
  description         = "Schedule for cost explorer report"
  schedule_expression = var.cost_report_schedule
}

# Target for the CloudWatch Event Rule
resource "aws_cloudwatch_event_target" "cost_explorer_target" {
  rule      = aws_cloudwatch_event_rule.cost_explorer_schedule.name
  target_id = "TriggerCostExplorerLambda"
  arn       = aws_lambda_function.cost_explorer.arn
}

# Permission to allow CloudWatch Events to invoke the Lambda function
resource "aws_lambda_permission" "allow_cloudwatch_cost_explorer" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_explorer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_explorer_schedule.arn
}

# Output the Lambda function ARN
output "cost_explorer_function_arn" {
  description = "The ARN of the Cost Explorer Lambda function"
  value       = aws_lambda_function.cost_explorer.arn
}
