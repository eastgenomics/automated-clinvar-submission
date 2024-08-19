"""
Script to monitor state of jobs launched by eggd_conductor, and notify
via Slack for any fails or when all successfully complete
"""
from datetime import datetime
import logging
import os
from requests import Session
from requests.adapters import HTTPAdapter
import sys
from urllib3.util import Retry
import argparse
from dotenv import load_dotenv

log = logging.getLogger("monitor log")
log.setLevel(logging.DEBUG)

log_format = logging.StreamHandler(sys.stdout)
log_format.setFormatter(
    logging.Formatter(
        "%(asctime)s:%(module)s:%(levelname)s: %(message)s"
    )
)
load_dotenv()
SLACK_TOKEN = os.getenv('SLACK_TOKEN')


def parse_args():
    """
    Parse arguments passed to the script

    Returns
    -------
    argparse.Namespace
        parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Monitor jobs launched by eggd_conductor"
    )
    parser.add_argument(
        '-c', '--channel', help="Slack channel to send notification to",
        type=str, required=True
    )
    parser.add_argument(
        '-o', '--outcome', help="outcome of job", type=str, required=True
    )
    parser.add_argument(
        '--fail-log-path', help="path to fail log file", type=str,
        required=True
    )
    parser.add_argument(
        '--pass-log-path', help="path to pass log file", type=str,
        required=True
    )
    parser.add_argument(
        '-T', '--testing', help="testing flag", action='store_true'
    )
    return parser.parse_args()


def read_log_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()


def filter_by_today(log_lines):
    today = datetime.now().strftime("%d/%m/%Y")
    return [line for line in log_lines if line.startswith(today)]


def count_metrics(fail_lines, pass_lines):
    total_wb_failed = len(fail_lines)
    total_wb_passed = len(pass_lines)
    total_wb_parsed = total_wb_failed + total_wb_passed
    return total_wb_parsed, total_wb_passed, total_wb_failed


def collate_wb_info(fail_log_path: str = 'workbooks_fail_to_parse.txt',
                    pass_log_path: str = 'workbooks_parsed_all_variants.txt'):

    fail_log_lines = read_log_file(fail_log_path)
    pass_log_lines = read_log_file(pass_log_path)

    today_fail_lines = filter_by_today(fail_log_lines)
    today_pass_lines = filter_by_today(pass_log_lines)

    total_parsed, total_passed, total_failed = count_metrics(
        today_fail_lines, today_pass_lines)

    return total_parsed, total_passed, total_failed


def test_notify(total_parsed, total_passed, total_failed):
    """
    Test function to test slack_notify function
    """
    print("Testing slack_notify function\n")
    print(f"total_parsed: {total_parsed}\n",
          f"total_passed: {total_passed}\n",
          f"total_failed: {total_failed}\n")


def slack_notify(channel, message, outcome, slack_token) -> None:
    """
    Send notification to given Slack channel

    Parameters
    ----------
    channel : str
        channel to send message to.
    message : str
        message to send to Slack.
    outcome : str
        "success" or "fail" to determine message color.
    slack_token : str
        Slack token to use for sending message.
    """
    log.info(f"Sending message to {channel}")
    slack_token = os.environ.get('SLACK_TOKEN')

    http = Session()
    retries = Retry(total=5, backoff_factor=10, method_whitelist=['POST'])
    http.mount("https://", HTTPAdapter(max_retries=retries))
    if outcome == 'success':
        message = f":white_check_mark: {message}"
    elif outcome == 'fail':
        message = f":warning: {message}"
    else:
        log.error(
            f"Invalid outcome {outcome} provided for slack notification"
        )
    try:
        response = http.post(
            'https://slack.com/api/chat.postMessage', {
                'token': slack_token,
                'channel': f"#{channel}",
                'text': message
            }).json()

        if not response['ok']:
            # error in sending slack notification
            log.error(
                f"Error in sending slack notification: {response.get('error')}"
            )
        else:
            # log job ID to know we sent an alert for it and not send another
            log.info(
                f"Successfully sent slack notification to {channel}"
            )
    except Exception as err:
        log.error(
            f"Error in sending post request for slack notification: {err}"
        )


def coordinate_notifications(parsed_args, outcome):
    """
    Coordinate notifications based on the parsed arguments.
    Args:
        parsed_args (argparse.Namespace): Parsed command-line arguments.
        outcome (str): Outcome of the automated job.
    Returns:
        None
    Raises:
        None
    """
    total_parsed, total_passed, total_failed = collate_wb_info(
        parsed_args.fail_log_path, parsed_args.pass_log_path
    )
    test_notify(total_parsed, total_passed, total_failed)
    # Logic to handle different messages
    if outcome == 'success':
        if total_failed > 0:
            message = (
                f"Automated parsing of sucessfully run."
                f":black_small_square: {total_parsed} workbooks parsed\n"
                f":black_small_square: {total_passed} passed\n"
                f":black_small_square: {total_failed} failed\n"
            )
            slack_notify(parsed_args.channel, message, 'success', SLACK_TOKEN)
        elif total_parsed == total_passed:
            message = (
                f"Automated parsing of sucessfully run."
                f":black_small_square: {total_parsed} workbooks parsed\n"
                f":black_small_square: {total_passed} passed\n"
                f":black_small_square: {total_failed} failed\n"
            )
            slack_notify(parsed_args.channel, message, 'success', SLACK_TOKEN)
        else:
            log.error("Invalid state to send slack notification")
        slack_notify(parsed_args.channel, message, 'success', SLACK_TOKEN)
    elif outcome == 'fail':
        message = f"Automated parsing of workbooks failed.\n Please check error logs. \n"
        if parsed_args.testing:
            parsed_args.channel = 'egg-test'  # override channel for testing
        else:
            parsed_args.channel = 'egg-test'  # override channel for testing
        slack_notify(parsed_args.channel, message, 'fail', SLACK_TOKEN)
    else:
        log.error("Invalid outcome provided for slack notification")
        message = (
            f"Error with Workbook parsing invalid outcome.\n"
            f"Please check run.\n"
            f":black_small_square: {total_parsed} workbooks parsed\n"
            f":black_small_square: {total_passed} passed\n"
            f":black_small_square: {total_failed} failed\n"
        )
        # slack_notify(parsed_args.channel, message, 'fail', SLACK_TOKEN)
    # if total_failed > 0:
    #     slack_notify(parsed_args.channel, message, 'fail', SLACK_TOKEN)
    # elif total_parsed == total_passed:
    #     slack_notify(parsed_args.channel, message, 'success', SLACK_TOKEN)
    # else:
    #     log.error("Invalid state to send slack notification")


def main():
    parsed_args = parse_args()
    coordinate_notifications(parsed_args, parsed_args.outcome)


if __name__ == "__main__":
    main()
