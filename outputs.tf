
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

# Output the IDs of the created test volumes
output "test_volume_ids" {
  description = "IDs of the test detached EBS volumes"
  value       = aws_ebs_volume.test_detached_volumes[*].id
}

# Output deletion time for test volumes
output "test_volumes_delete_after" {
  description = "Date after which test volumes can be safely deleted"
  value       = var.create_test_resources ? formatdate("YYYY-MM-DD", timeadd(timestamp(), "${var.test_retention_days * 24}h")) : "No test volumes created"
}
