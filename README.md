# AWS Cost Optimization - Detached EBS Volumes Monitor

An automated solution to identify detached (unused) EBS volumes in your AWS account and send email notifications for potential cost savings.

## Features

- Automated detection of detached EBS volumes that have been unused for a configurable period
- Cost estimation based on volume type and size
- Email notifications with detailed information and cost analysis
- Scheduled execution via AWS CloudWatch Events
- Infrastructure-as-Code deployment using OpenTofu (Terraform compatible)

## Architecture

The architecture diagram is available in the `img/architecture.txt` file. When pushed to GitHub, it will render automatically as a Mermaid diagram.

1. CloudWatch Events trigger the Lambda function on a schedule
2. Lambda scans for detached EBS volumes across all regions
3. If detached volumes are found, Lambda sends an email alert via SES
4. Infrastructure is managed via OpenTofu/Terraform

## Prerequisites

- [OpenTofu](https://opentofu.org/docs/intro/install/) or [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) installed
- [Task](https://taskfile.dev/#/installation) for running the Taskfile
- AWS CLI configured with appropriate credentials
- Python 3.9+ (for local development/testing)
- SES email identity verification

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
- Scheduling frequency
- Threshold for detached volume days

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

- `task test-lambda`: Run the Lambda function locally with test data
- `task create-test-volumes`: Create test detached EBS volumes for real-world testing
- `task destroy-test-volumes`: Remove the test volumes when done testing

## Customization

### Adjusting the Detection Threshold

To change how many days a volume must be detached before alerting, modify the `days_threshold` variable in `terraform.tfvars`.

### Changing the Schedule

Modify the `schedule_expression` variable in `terraform.tfvars` to change when the function runs. Uses standard CloudWatch Events cron syntax.

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
