import boto3
import os
from datetime import datetime, timezone
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to identify detached EBS volumes and send email alerts.
    """
    # Environment variables
    sender_email = os.environ.get('SENDER_EMAIL')
    recipient_emails = os.environ.get('RECIPIENT_EMAILS', '').split(',')
    days_threshold = int(os.environ.get('DAYS_THRESHOLD', '7'))

    # Get the AWS region from the Lambda context instead of environment variable
    aws_region = context.invoked_function_arn.split(':')[3]

    if not sender_email or not recipient_emails:
        print("Missing required environment variables: SENDER_EMAIL and RECIPIENT_EMAILS")
        return {
            'statusCode': 500,
            'body': 'Missing required environment variables'
        }

    # Initialize AWS clients
    ec2_client = boto3.client('ec2', region_name=aws_region)
    ses_client = boto3.client('ses', region_name=aws_region)

    # Find detached EBS volumes
    detached_volumes = find_detached_volumes(ec2_client, days_threshold)

    if not detached_volumes:
        print("No detached volumes found.")
        return {
            'statusCode': 200,
            'body': 'No detached volumes found'
        }

    # Send email alert
    send_email_alert(ses_client, detached_volumes, sender_email, recipient_emails, aws_region)

    return {
        'statusCode': 200,
        'body': f'Found {len(detached_volumes)} detached volumes and sent email alert'
    }

def find_detached_volumes(ec2_client, days_threshold):
    """
    Find EBS volumes that are available (not attached) for more than the specified days.
    """
    now = datetime.now(timezone.utc)
    detached_volumes = []

    try:
        # Get all available volumes
        response = ec2_client.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )

        # Process each volume
        for volume in response.get('Volumes', []):
            volume_id = volume.get('VolumeId')
            create_time = volume.get('CreateTime')
            size = volume.get('Size')
            volume_type = volume.get('VolumeType')

            # Calculate days since creation
            days_available = (now - create_time).days

            # Calculate monthly cost (estimation)
            monthly_cost = estimate_volume_cost(size, volume_type)

            # Add volumes that exceed the threshold
            if days_available >= days_threshold:
                tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])} if 'Tags' in volume else {}

                detached_volumes.append({
                    'VolumeId': volume_id,
                    'Size': size,
                    'VolumeType': volume_type,
                    'DaysAvailable': days_available,
                    'EstimatedMonthlyCost': monthly_cost,
                    'Tags': tags,
                    'AvailabilityZone': volume.get('AvailabilityZone')
                })

        return detached_volumes

    except ClientError as e:
        print(f"Error finding detached volumes: {e}")
        raise

def estimate_volume_cost(size, volume_type):
    """
    Estimate monthly cost of EBS volume (simplified calculation).
    Prices are approximations and may vary by region.
    """
    # Simplified pricing (USD per GB-month)
    pricing = {
        'gp2': 0.10,
        'gp3': 0.08,
        'io1': 0.125,
        'io2': 0.125,
        'st1': 0.045,
        'sc1': 0.025,
        'standard': 0.05
    }

    rate = pricing.get(volume_type.lower(), 0.10)  # Default to gp2 pricing
    return round(size * rate, 2)

def send_email_alert(ses_client, detached_volumes, sender_email, recipient_emails, region):
    """
    Send email alert with details of detached volumes.
    """
    # Calculate total cost
    total_cost = sum(volume['EstimatedMonthlyCost'] for volume in detached_volumes)

    # Generate HTML table for email
    volume_rows = ""
    for volume in detached_volumes:
        name_tag = volume['Tags'].get('Name', 'N/A')
        volume_rows += f"""
        <tr>
            <td>{volume['VolumeId']}</td>
            <td>{name_tag}</td>
            <td>{volume['Size']} GB</td>
            <td>{volume['VolumeType']}</td>
            <td>{volume['DaysAvailable']}</td>
            <td>${volume['EstimatedMonthlyCost']:.2f}</td>
            <td>{volume['AvailabilityZone']}</td>
        </tr>
        """

    # Construct email body
    html_body = f"""
    <html>
    <head>
        <style>
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .summary {{
                margin-top: 20px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h2>Detached EBS Volumes Alert</h2>
        <p>The following EBS volumes have been detached for an extended period and may be candidates for cleanup:</p>

        <table>
            <tr>
                <th>Volume ID</th>
                <th>Name</th>
                <th>Size</th>
                <th>Type</th>
                <th>Days Detached</th>
                <th>Est. Monthly Cost</th>
                <th>AZ</th>
            </tr>
            {volume_rows}
        </table>

        <div class="summary">
            <p>Total Estimated Monthly Cost: ${total_cost:.2f}</p>
            <p>Potential Annual Savings: ${total_cost * 12:.2f}</p>
        </div>

        <p>To clean up these volumes, visit the <a href="https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}#Volumes">EC2 Console</a>.</p>

        <p><small>This is an automated message from the AWS Cost Optimization system.</small></p>
    </body>
    </html>
    """

    # Construct email subject
    subject = f"[AWS Cost Alert] {len(detached_volumes)} Detached EBS Volumes Found (${total_cost:.2f}/month)"

    try:
        # Send email
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': recipient_emails
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        'Data': html_body
                    }
                }
            }
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
        return True

    except ClientError as e:
        print(f"Error sending email: {e}")
        raise
