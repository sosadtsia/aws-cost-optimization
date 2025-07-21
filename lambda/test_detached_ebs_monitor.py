import unittest
from unittest.mock import patch, MagicMock
import os
from datetime import datetime, timezone, timedelta
import detached_ebs_monitor

class TestDetachedEBSMonitor(unittest.TestCase):

    def setUp(self):
        # Set up environment variables for testing
        os.environ['SENDER_EMAIL'] = 'test@example.com'
        os.environ['RECIPIENT_EMAILS'] = 'admin@example.com,finance@example.com'
        os.environ['DAYS_THRESHOLD'] = '7'

    @patch('detached_ebs_monitor.boto3.client')
    def test_find_detached_volumes(self, mock_boto_client):
        # Mock EC2 client
        mock_ec2 = MagicMock()
        mock_boto_client.return_value = mock_ec2

        # Set up mock response
        now = datetime.now(timezone.utc)
        old_volume_date = now - timedelta(days=10)
        new_volume_date = now - timedelta(days=2)

        mock_ec2.describe_volumes.return_value = {
            'Volumes': [
                {
                    'VolumeId': 'vol-12345',
                    'Size': 100,
                    'VolumeType': 'gp2',
                    'AvailabilityZone': 'us-east-1a',
                    'CreateTime': old_volume_date,
                    'Tags': [{'Key': 'Name', 'Value': 'Old Volume'}]
                },
                {
                    'VolumeId': 'vol-67890',
                    'Size': 50,
                    'VolumeType': 'gp3',
                    'AvailabilityZone': 'us-east-1b',
                    'CreateTime': new_volume_date,
                    'Tags': [{'Key': 'Name', 'Value': 'New Volume'}]
                }
            ]
        }

        # Call the function
        result = detached_ebs_monitor.find_detached_volumes(mock_ec2, 7)

        # Verify results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['VolumeId'], 'vol-12345')
        self.assertEqual(result[0]['Size'], 100)
        self.assertEqual(result[0]['Tags']['Name'], 'Old Volume')

        # Verify the function called EC2 client correctly
        mock_ec2.describe_volumes.assert_called_once_with(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )

    def test_estimate_volume_cost(self):
        # Test cost calculation for different volume types
        self.assertEqual(detached_ebs_monitor.estimate_volume_cost(100, 'gp2'), 10.0)
        self.assertEqual(detached_ebs_monitor.estimate_volume_cost(100, 'gp3'), 8.0)
        self.assertEqual(detached_ebs_monitor.estimate_volume_cost(100, 'io1'), 12.5)
        self.assertEqual(detached_ebs_monitor.estimate_volume_cost(50, 'st1'), 2.25)

    @patch('detached_ebs_monitor.boto3.client')
    def test_lambda_handler_no_volumes(self, mock_boto_client):
        # Mock EC2 and SES clients
        mock_ec2 = MagicMock()
        mock_ses = MagicMock()

        def get_mock_client(service, **kwargs):
            if service == 'ec2':
                return mock_ec2
            elif service == 'ses':
                return mock_ses

        mock_boto_client.side_effect = get_mock_client

        # Set up EC2 response with no volumes
        mock_ec2.describe_volumes.return_value = {'Volumes': []}

        # Mock Lambda context
        mock_context = MagicMock()
        mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"

        # Call lambda handler
        result = detached_ebs_monitor.lambda_handler({}, mock_context)

        # Verify the result and that SES was not called
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['body'], 'No detached volumes found')
        mock_ses.send_email.assert_not_called()

    @patch('detached_ebs_monitor.find_detached_volumes')
    @patch('detached_ebs_monitor.send_email_alert')
    @patch('detached_ebs_monitor.boto3.client')
    def test_lambda_handler_with_volumes(self, mock_boto_client, mock_send_email, mock_find_volumes):
        # Mock EC2 and SES clients
        mock_ec2 = MagicMock()
        mock_ses = MagicMock()

        def get_mock_client(service, **kwargs):
            if service == 'ec2':
                return mock_ec2
            elif service == 'ses':
                return mock_ses

        mock_boto_client.side_effect = get_mock_client

        # Set up volumes result
        mock_volumes = [
            {
                'VolumeId': 'vol-12345',
                'Size': 100,
                'VolumeType': 'gp2',
                'DaysAvailable': 10,
                'EstimatedMonthlyCost': 10.0,
                'Tags': {'Name': 'Test Volume'},
                'AvailabilityZone': 'us-east-1a'
            }
        ]
        mock_find_volumes.return_value = mock_volumes

        # Mock Lambda context
        mock_context = MagicMock()
        mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"

        # Call lambda handler
        result = detached_ebs_monitor.lambda_handler({}, mock_context)

        # Verify the result
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['body'], 'Found 1 detached volumes and sent email alert')

        # Verify email was sent
        mock_send_email.assert_called_once_with(
            mock_ses, mock_volumes, 'test@example.com',
            ['admin@example.com', 'finance@example.com'], 'us-east-1'
        )

if __name__ == '__main__':
    unittest.main()
