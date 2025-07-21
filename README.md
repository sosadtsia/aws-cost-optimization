# AWS Cost Optimization

A comprehensive AWS cost optimization solution with two key components:
1. Detached EBS Volume Monitor - identifies unused EBS volumes and sends alerts
2. Cost Explorer Dashboard - provides detailed cost analysis and recommendations

## Features

### EBS Volume Monitor
- Automated detection of detached EBS volumes that have been unused for a configurable period
- Cost estimation based on volume type and size
- Email notifications with detailed information and cost analysis
- Scheduled execution via AWS CloudWatch Events
- Infrastructure-as-Code deployment using OpenTofu (Terraform compatible)

### Cost Explorer Dashboard
- Comprehensive AWS cost analysis using the Cost Explorer API
- Service cost breakdown with top spending areas
- Storage cost analysis (EBS, S3, RDS, etc.)
- Trend detection and budget threshold alerts
- Rich HTML email reports with cost optimization recommendations

## Architecture

The system consists of two separate Lambda functions, each with its own CloudWatch trigger and IAM permissions:

1. **Detached EBS Volume Monitor**: Scans for detached volumes and sends alerts
2. **Cost Explorer Dashboard**: Analyzes AWS costs and generates reports

## Prerequisites

- [OpenTofu](https://opentofu.org/docs/intro/install/) or [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) installed
- [Task](https://taskfile.dev/#/installation) for running the Taskfile
- AWS CLI configured with appropriate credentials
- Python 3.9+ (for local development/testing)
- SES email identity verification
- Cost Explorer API enabled (enabled by default in most AWS accounts)

## Deployment

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/aws-cost-optimization.git
cd aws-cost-optimization
```

### 2. Configure the settings

Copy the example configuration file and edit it with your settings:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` to configure:
- AWS region
- Sender email address (must be verified in SES)
- Recipient email addresses
- Scheduling frequency for both monitors
- Budget threshold for cost alerts
- Days threshold for detached volume alerts

### 3. Deploy with Task

To deploy all resources, run:

```bash
task all
task apply
```

After deployment, verify your SES email identity:

```bash
task verify-ses
```

## Task Commands

The project includes a Taskfile.yml with the following commands:

- `task setup`: Initial setup, creates terraform.tfvars from example
- `task init`: Initialize OpenTofu/Terraform
- `task validate`: Validate OpenTofu/Terraform configuration
- `task plan`: Create an execution plan
- `task apply`: Apply the changes and deploy resources
- `task destroy`: Remove all resources
- `task package`: Package the Lambda function code
- `task test-python`: Lint the Python code
- `task verify-ses`: Instructions for verifying SES email
- `task all`: Run the full deployment pipeline

### Testing Commands

- `task test-ebs-lambda`: Test the EBS volume monitor Lambda function locally
- `task test-cost-lambda`: Test the Cost Explorer Lambda function locally
- `task create-test-volumes`: Create test detached EBS volumes for real-world testing
- `task destroy-test-volumes`: Remove the test volumes when done testing

## Customization

### EBS Volume Monitor

#### Adjusting the Detection Threshold

To change how many days a volume must be detached before alerting, modify the `days_threshold` variable in `terraform.tfvars`.

#### Changing the Schedule

Modify the `schedule_expression` variable in `terraform.tfvars` to change when the function runs. Uses standard CloudWatch Events cron syntax.

### Cost Explorer Dashboard

#### Setting a Budget Threshold

To enable budget alerts, set a non-zero value for the `budget_threshold` variable in `terraform.tfvars`.

#### Changing the Reporting Period

Modify the `report_period_days` variable in `terraform.tfvars` to change the number of days included in the cost report.

#### Adjusting the Schedule

Modify the `cost_report_schedule` variable in `terraform.tfvars` to change when the cost reports are generated.

### Testing with Real Volumes

To test with real detached EBS volumes:

1. Update `terraform.tfvars` with your preferred test settings:
   ```
   create_test_resources = true  # Enable test volume creation
   test_volume_count     = 3     # Number of volumes to create
   test_volume_size      = 5     # Size in GB
   test_retention_days   = 14    # Days to keep before suggesting deletion
   ```

2. Run `task create-test-volumes` to create detached volumes
3. Invoke the Lambda function to test detection
4. Run `task destroy-test-volumes` to clean up when done

## Cost Impact

This solution costs very little to run:
- AWS Lambda: Free tier includes 1M free requests per month
- CloudWatch Events: $1.00 per million custom events
- SES: Free tier includes 62,000 outbound messages per month when sent from EC2 or Lambda
- Cost Explorer API: First 1,000 requests per month are free

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
