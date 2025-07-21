import boto3
import os
import json
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to generate AWS cost analysis reports and send email alerts.
    """
    # Environment variables
    sender_email = os.environ.get('SENDER_EMAIL')
    recipient_emails = os.environ.get('RECIPIENT_EMAILS', '').split(',')
    report_period_days = int(os.environ.get('REPORT_PERIOD_DAYS', '30'))
    budget_threshold = float(os.environ.get('BUDGET_THRESHOLD', '0'))

    # Get the AWS region from the Lambda context
    aws_region = context.invoked_function_arn.split(':')[3]

    if not sender_email or not recipient_emails:
        print("Missing required environment variables: SENDER_EMAIL and RECIPIENT_EMAILS")
        return {
            'statusCode': 500,
            'body': 'Missing required environment variables'
        }

    # Initialize AWS clients
    ce_client = boto3.client('ce', region_name=aws_region)
    ses_client = boto3.client('ses', region_name=aws_region)

    try:
        # Get cost data
        cost_data = get_cost_data(ce_client, report_period_days)
        service_costs = get_service_breakdown(ce_client, report_period_days)
        storage_costs = get_storage_costs(ce_client, report_period_days)

        # Generate budget alerts if needed
        budget_alerts = []
        if budget_threshold > 0:
            budget_alerts = check_budget_alerts(cost_data, budget_threshold)

        # Send email report
        send_cost_report(
            ses_client,
            cost_data,
            service_costs,
            storage_costs,
            budget_alerts,
            sender_email,
            recipient_emails,
            aws_region
        )

        return {
            'statusCode': 200,
            'body': 'Cost report generated and sent successfully'
        }

    except Exception as e:
        print(f"Error generating cost report: {e}")
        return {
            'statusCode': 500,
            'body': f'Error generating cost report: {str(e)}'
        }

def get_cost_data(ce_client, days):
    """
    Get cost data for the specified period using the Cost Explorer API.
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Get daily costs
    daily_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    # Get monthly costs
    monthly_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    # Get trend (compare to previous period)
    previous_start = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
    previous_end = start_date

    trend_current = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    trend_previous = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': previous_start,
            'End': previous_end
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    # Calculate total costs and trend
    current_total = sum(float(day['Total']['UnblendedCost']['Amount'])
                       for day in trend_current['ResultsByTime'])

    previous_total = sum(float(day['Total']['UnblendedCost']['Amount'])
                        for day in trend_previous['ResultsByTime'])

    trend_percentage = ((current_total - previous_total) / previous_total * 100) if previous_total > 0 else 0

    return {
        'daily_data': daily_response,
        'monthly_data': monthly_response,
        'start_date': start_date,
        'end_date': end_date,
        'current_total': current_total,
        'previous_total': previous_total,
        'trend_percentage': trend_percentage
    }

def get_service_breakdown(ce_client, days):
    """
    Get cost breakdown by service.
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    # Extract service costs from the response
    service_costs = []

    for time_period in response['ResultsByTime']:
        for group in time_period['Groups']:
            service_name = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            service_costs.append({
                'service': service_name,
                'cost': amount
            })

    # Sort by cost (descending)
    service_costs.sort(key=lambda x: x['cost'], reverse=True)

    return service_costs[:10]  # Return top 10 services

def get_storage_costs(ce_client, days):
    """
    Get detailed breakdown of storage costs (EBS, S3, etc.)
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Define storage services to track
    storage_services = ['Amazon Elastic Block Store', 'Amazon Simple Storage Service',
                        'Amazon RDS Service', 'Amazon DynamoDB', 'AWS Backup']

    # Create a filter for storage services
    response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        Filter={
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': storage_services
            }
        },
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    # Extract storage costs from the response
    storage_costs = []

    for time_period in response['ResultsByTime']:
        for group in time_period.get('Groups', []):
            service_name = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            storage_costs.append({
                'service': service_name,
                'cost': amount
            })

    # If no storage costs are found
    if len(storage_costs) == 0:
        # Try without filter to see if there are any storage costs at all
        try:
            basic_response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            # Just note that no storage costs were found
            storage_costs = [{
                'service': 'No specific storage costs found',
                'cost': 0
            }]
        except Exception as e:
            print(f"Error getting basic cost data: {e}")
            storage_costs = [{
                'service': 'Error retrieving storage costs',
                'cost': 0
            }]

    return storage_costs

def check_budget_alerts(cost_data, budget_threshold):
    """
    Check if current spending exceeds budget threshold and generate alerts.
    """
    current_total = cost_data['current_total']
    alerts = []

    # Check if current spending exceeds budget
    if current_total > budget_threshold:
        percentage_over = ((current_total - budget_threshold) / budget_threshold) * 100
        alerts.append({
            'type': 'Budget Exceeded',
            'message': f'Current spending (${current_total:.2f}) exceeds budget threshold (${budget_threshold:.2f}) by {percentage_over:.1f}%',
            'severity': 'high'
        })

    # Check if the trend is significantly increasing
    if cost_data['trend_percentage'] > 20:
        alerts.append({
            'type': 'Spending Trend',
            'message': f'Spending increased by {cost_data["trend_percentage"]:.1f}% compared to the previous period',
            'severity': 'medium'
        })

    return alerts

def send_cost_report(ses_client, cost_data, service_costs, storage_costs, budget_alerts, sender_email, recipient_emails, region):
    """
    Send email with cost analysis report.
    """
    # Generate service cost rows for the email
    service_rows = ""
    for service in service_costs:
        service_rows += f"""
        <tr>
            <td>{service['service']}</td>
            <td>${service['cost']:.2f}</td>
        </tr>
        """

    # Generate storage cost rows for the email
    storage_rows = ""
    for storage in storage_costs:
        storage_rows += f"""
        <tr>
            <td>{storage['service']}</td>
            <td>${storage['cost']:.2f}</td>
        </tr>
        """

    # Generate alert boxes if needed
    alerts_html = ""
    if budget_alerts:
        for alert in budget_alerts:
            color = "red" if alert['severity'] == 'high' else "orange"
            alerts_html += f"""
            <div style="background-color: {color}; color: white; padding: 10px; margin: 10px 0; border-radius: 5px;">
                <strong>{alert['type']}:</strong> {alert['message']}
            </div>
            """

    # Calculate trend indicator
    trend_indicator = "↑" if cost_data['trend_percentage'] > 0 else "↓"
    trend_color = "red" if cost_data['trend_percentage'] > 0 else "green"

    # Generate cost trends for charting (simplified as text-based visualization)
    month_costs = []
    for month in cost_data['monthly_data']['ResultsByTime']:
        amount = float(month['Total']['UnblendedCost']['Amount'])
        month_costs.append(amount)

    trend_values = ", ".join([f"${cost:.2f}" for cost in month_costs])

    # Construct email body
    html_body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
            }}
            .header {{
                background-color: #0275d8;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                padding: 20px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .summary {{
                background-color: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #0275d8;
            }}
            .trend-up {{
                color: red;
            }}
            .trend-down {{
                color: green;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 0.8em;
                text-align: center;
                color: #777;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>AWS Cost Explorer Report</h2>
            <p>Period: {cost_data['start_date']} to {cost_data['end_date']}</p>
        </div>

        <div class="content">
            {alerts_html}

            <div class="summary">
                <h3>Cost Summary</h3>
                <p>Total Cost: <strong>${cost_data['current_total']:.2f}</strong></p>
                <p>Trend: <span style="color: {trend_color}">{trend_indicator} {abs(cost_data['trend_percentage']):.1f}%</span> compared to previous period</p>
                <p>Previous Period: ${cost_data['previous_total']:.2f}</p>
            </div>

            <h3>Top Services by Cost</h3>
            <table>
                <tr>
                    <th>Service</th>
                    <th>Cost</th>
                </tr>
                {service_rows}
            </table>

            <h3>Storage Costs Breakdown</h3>
            <table>
                <tr>
                    <th>Storage Type</th>
                    <th>Cost</th>
                </tr>
                {storage_rows}
            </table>

            <h3>Cost Optimization Recommendations</h3>
            <ul>
                <li>Check for unused EBS volumes and delete them if not needed</li>
                <li>Review right-sizing recommendations for EC2 instances</li>
                <li>Consider using Savings Plans or Reserved Instances for consistent workloads</li>
                <li>Set up S3 lifecycle policies to move infrequently accessed data to cheaper storage tiers</li>
                <li>Review and terminate development/testing resources during off-hours</li>
            </ul>

            <p>View detailed cost analysis in the <a href="https://{region}.console.aws.amazon.com/cost-management/home">AWS Cost Explorer Console</a>.</p>
        </div>

        <div class="footer">
            <p>This is an automated message from the AWS Cost Explorer Dashboard system.</p>
        </div>
    </body>
    </html>
    """

    # Construct email subject
    trend_text = "increased" if cost_data['trend_percentage'] > 0 else "decreased"
    subject = f"AWS Cost Report - ${cost_data['current_total']:.2f} ({trend_text} by {abs(cost_data['trend_percentage']):.1f}%)"

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
