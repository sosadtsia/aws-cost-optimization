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
