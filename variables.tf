variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "detached-ebs-monitor"
}

variable "sender_email" {
  description = "Verified SES email address to send alerts from"
  type        = string
}

variable "recipient_emails" {
  description = "List of email addresses to send alerts to"
  type        = list(string)
}

variable "days_threshold" {
  description = "Number of days a volume must be detached before alerting"
  type        = number
  default     = 7
}

variable "schedule_expression" {
  description = "CloudWatch Events schedule expression for running the Lambda"
  type        = string
  default     = "cron(0 9 ? * MON *)" # Run every Monday at 9:00 AM UTC
}

# Test resources configuration
variable "create_test_resources" {
  description = "Whether to create test detached EBS volumes"
  type        = bool
  default     = false
}

variable "test_volume_count" {
  description = "Number of test detached EBS volumes to create"
  type        = number
  default     = 3
}

variable "test_volume_size" {
  description = "Size in GB of each test detached EBS volume"
  type        = number
  default     = 5
}

variable "test_retention_days" {
  description = "Number of days to keep test volumes before recommending deletion"
  type        = number
  default     = 14
}
