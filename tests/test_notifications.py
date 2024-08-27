"""
Test cases for slack_notifications.py
"""
import unittest
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
import os
import json
import sys
import argparse

from unittest.mock import patch, Mock
import logging
sys.path.append('utils/')

from slack_notifications import (
    parse_args, read_log_file, filter_by_today, count_metrics,
    collate_wb_info, slack_notify_webhook, coordinate_notifications
)

# Mock logging
log = logging.getLogger('slack_notifications')
log.setLevel(logging.DEBUG)


class TestSlackNotifications(unittest.TestCase):

    @patch.dict(os.environ, {'SLACK_WEBHOOK_URL': 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'})
    def test_parse_args(self):
        test_args = [
            'script_name', '-c', 'egg-test', '-o', 'success',
            '--fail-log-path', 'fail_log.txt', '--pass-log-path', 'pass_log.txt'
        ]
        with patch('sys.argv', test_args):
            args = parse_args()
            self.assertEqual(args.channel, 'egg-test')
            self.assertEqual(args.outcome, 'success')
            self.assertEqual(args.fail_log_path, 'fail_log.txt')
            self.assertEqual(args.pass_log_path, 'pass_log.txt')

    @patch('builtins.open', new_callable=mock_open, read_data='line1\nline2\n')
    def test_read_log_file(self, mock_file):
        lines = read_log_file('dummy_path')
        self.assertEqual(lines, ['line1\n', 'line2\n'])

    @patch('slack_notifications.datetime')
    def test_filter_by_today(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 10, 1)
        mock_datetime.strftime.return_value = '01/10/2023'
        log_lines = ['01/10/2023 log entry', '30/09/2023 log entry']
        filtered_lines = filter_by_today(log_lines)
        self.assertEqual(filtered_lines, ['01/10/2023 log entry'])

    def test_read_log_file_empty(self):
        with patch('builtins.open', new_callable=mock_open, read_data=''):
            lines = read_log_file('dummy_path')
            self.assertEqual(lines, [])

    def test_filter_by_today_empty(self):
        with patch('slack_notifications.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 10, 1)
            mock_datetime.strftime.return_value = '01/10/2023'
            log_lines = []
            filtered_lines = filter_by_today(log_lines)
            self.assertEqual(filtered_lines, [])

    def test_count_metrics_empty(self):
        fail_lines = []
        pass_lines = []
        total_parsed, total_passed, total_failed = count_metrics(
            fail_lines, pass_lines)
        self.assertEqual(total_parsed, 0)
        self.assertEqual(total_passed, 0)
        self.assertEqual(total_failed, 0)

    def test_coordinate_notifications_failure(self):
        with patch('slack_notifications.collate_wb_info') as mock_collate_wb_info, \
                patch('slack_notifications.slack_notify_webhook') as mock_slack_notify_webhook:
            mock_collate_wb_info.return_value = (10, 8, 2)
            parsed_args = argparse.Namespace(
                channel='egg-test', outcome='failure',
                fail_log_path='fail_log.txt', pass_log_path='pass_log.txt',
                testing=False
            )
            coordinate_notifications(parsed_args, 'failure')
            mock_slack_notify_webhook.assert_called_once()

    def test_count_metrics(self):
        fail_lines = ['fail1', 'fail2']
        pass_lines = ['pass1', 'pass2', 'pass3']
        total_parsed, total_passed, total_failed = count_metrics(
            fail_lines, pass_lines)
        self.assertEqual(total_parsed, 5)
        self.assertEqual(total_passed, 3)
        self.assertEqual(total_failed, 2)

    @patch('slack_notifications.read_log_file')
    @patch('slack_notifications.filter_by_today')
    def test_collate_wb_info(self, mock_filter_by_today, mock_read_log_file):
        mock_read_log_file.side_effect = [
            ['01/10/2023 fail1', '01/10/2023 fail2'],
            ['01/10/2023 pass1', '01/10/2023 pass2', '01/10/2023 pass3']
        ]
        mock_filter_by_today.side_effect = lambda x: x
        total_parsed, total_passed, total_failed = collate_wb_info(
            'fail_log.txt', 'pass_log.txt')
        self.assertEqual(total_parsed, 5)
        self.assertEqual(total_passed, 3)
        self.assertEqual(total_failed, 2)

    @patch('requests.Session.post')
    def test_slack_notify_webhook(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        slack_notify_webhook('Test message', 'success',
                             'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX')
        mock_post.assert_called_once_with(
            'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
            data=json.dumps({"text": ":white_check_mark: Test message"}),
            headers={'Content-Type': 'application/json'}
        )

    @patch('slack_notifications.collate_wb_info')
    @patch('slack_notifications.slack_notify_webhook')
    def test_coordinate_notifications(self, mock_slack_notify_webhook, mock_collate_wb_info):
        mock_collate_wb_info.return_value = (10, 8, 2)
        parsed_args = argparse.Namespace(
            channel='egg-test', outcome='success',
            fail_log_path='fail_log.txt', pass_log_path='pass_log.txt',
            testing=False
        )
        coordinate_notifications(parsed_args, 'success')
        mock_slack_notify_webhook.assert_called_once()


class TestSlackNotifier(unittest.TestCase):
    @patch('slack_notifications.Session.post')
    def test_slack_notify_webhook_success(self, mock_post):
        # Mock a successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch('slack_notifications.log') as mock_log:
            slack_notify_webhook('Test message', 'success',
                                 'http://fake-webhook-url')
            mock_log.info.assert_called_with(
                "Successfully sent slack notification")

    @patch('slack_notifications.Session.post')
    def test_slack_notify_webhook_fail(self, mock_post):
        # Mock a failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with patch('slack_notifications.log') as mock_log:
            slack_notify_webhook(
                'Test message', 'wrong_outcome', 'http://fake-webhook-url')
            print(mock_log.error)
            mock_log.error.assert_called_with(
                f"Error in sending slack notification: {mock_post.return_value.text}")

    @patch('slack_notifications.Session.post')
    def test_slack_notify_webhook_invalid_outcome(self, mock_post):
        # Mock a failed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch('slack_notifications.log') as mock_log:
            slack_notify_webhook('Test message', 'invalid',
                                 'http://fake-webhook-url')
            mock_log.error.assert_called_with(
                "Invalid outcome invalid provided for slack notification")

    @patch('slack_notifications.collate_wb_info')
    @patch('slack_notifications.slack_notify_webhook')
    def test_coordinate_notifications(self, mock_slack_notify_webhook, mock_collate_wb_info):
        mock_collate_wb_info.return_value = (10, 8, 2)
        parsed_args = argparse.Namespace(
            channel='egg-test', outcome='success',
            fail_log_path='fail_log.txt', pass_log_path='pass_log.txt',
            testing=False
        )
        coordinate_notifications(parsed_args, 'success')
        mock_slack_notify_webhook.assert_called_once()


if __name__ == '__main__':
    unittest.main()
