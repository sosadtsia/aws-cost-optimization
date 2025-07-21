# Test resources for the detached EBS volume monitor
# This file creates test EBS volumes that are intentionally detached
# to test the Lambda function's ability to detect them.

# Only create test resources if enabled
locals {
  create_test_resources = var.create_test_resources ? 1 : 0
}

# Get available AZs in the current region
data "aws_availability_zones" "available" {
  state = "available"
}

# Create detached EBS volumes for testing
resource "aws_ebs_volume" "test_detached_volumes" {
  count             = local.create_test_resources * var.test_volume_count
  availability_zone = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]
  size              = var.test_volume_size
  type              = count.index % 2 == 0 ? "gp3" : "gp2" # Alternate between volume types

  tags = {
    Name        = "test-detached-volume-${count.index + 1}"
    environment = var.environment
    project     = var.project_name
    createdBy   = "OpenTofu"
    purpose     = "Testing EBS volume detection"
    DeleteAfter = formatdate("YYYY-MM-DD", timeadd(timestamp(), "${var.test_retention_days * 24}h"))
  }

  lifecycle {
    create_before_destroy = true
  }
}
