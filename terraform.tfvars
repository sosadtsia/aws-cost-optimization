aws_region       = "us-east-2"
environment      = "develop"
project_name     = "detached-ebs-monitor"
sender_email     = "your-verified-email@example.com"
recipient_emails = ["svos022009@gmail.com"]
days_threshold   = 7
schedule_expression = "cron(0 9 ? * MON *)" # Run every Monday at 9:00 AM UTC

create_test_resources = true  # Enable test volume creation
test_volume_count     = 3     # Number of volumes to create (adjust as needed)
test_volume_size      = 2     # Size in GB (keep small to minimize costs)
test_retention_days   = 1     # Days to keep before suggesting deletion
