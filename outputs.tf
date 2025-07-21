
# Optional: Output the Lambda function ARN
output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.detached_ebs_monitor.arn
}

# Optional: Output for verification guidance
output "ses_verification_guidance" {
  description = "Instructions for verifying SES email"
  value       = "Remember to verify your sender email ${var.sender_email} through the AWS SES console"
}
