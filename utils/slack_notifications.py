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
import json

logging.basicConfig(
    filename="/tmp/auto_clinvar_slack_notify.log",
    encoding="utf-8",
    filemode="a",
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO
)
log = logging.getLogger("monitor log")


def parse_args():
    """
    Parse arguments passed to the script

    Returns
    -------
    argparse.Namespace
        parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Raising slack notifications for automated clinvar submission"
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

    return parser.parse_args()


def read_log_file(file_path):
    """
    Read log file and return lines.

    Parameters
    ----------
    file_path : str
        The path to the log file.

    Returns
    -------
    list
        List of lines in the log file.
    """
    with open(file_path, 'r') as file:
        return file.readlines()


def filter_by_today(log_lines):
    """
    Filter log lines by today's date.

    Parameters
    ----------
    log_lines : list
        logfile lines imported from the log file

    Returns
    -------
    list
        List of log lines that start with today's date.
    """
    today = datetime.now().strftime("%d/%m/%Y")
    return [line for line in log_lines if line.startswith(today)]


def count_metrics(fail_lines, pass_lines):
    """
    Count the total number of workbooks parsed, passed, and failed.

    Parameters
    ----------
    fail_lines : list
        logfile lines imported from the fail log file

    pass_lines : list
        logfile lines imported from the pass log file

    Returns
    -------
    total_wb_parsed : int
        The total number of workbooks parsed.
    total_wb_passed : int
        The total number of workbooks that passed.
    total_wb_failed : int
        The total number of workbooks that failed.
    """
    total_wb_failed = len(fail_lines)
    total_wb_passed = len(pass_lines)
    total_wb_parsed = total_wb_failed + total_wb_passed
    return total_wb_parsed, total_wb_passed, total_wb_failed


def collate_wb_info(fail_log_path: str = 'workbooks_fail_to_parse.txt',
                    pass_log_path: str = 'workbooks_parsed_all_variants.txt'):
    """
    Collates workbook information and returns the total parsed,
        total passed, and total failed metrics.

    Parameters
    ----------
    fail_log_path : str, optional, by default 'workbooks_fail_to_parse.txt'
        The file path to the log file containing the workbooks that failed to parse.
        Default is 'workbooks_fail_to_parse.txt'.
    pass_log_path : str, optional, by default 'workbooks_parsed_all_variants.txt'
        The file path to the log file containing the workbooks
            with all parsed variants.
        Default is 'workbooks_parsed_all_variants.txt'.

    Returns
    -------
    total_parsed : int
        The total number of workbooks parsed.
    total_passed : int
        The total number of workbooks that passed.
    total_failed : int
        The total number of workbooks that failed.
    """

    fail_log_lines = read_log_file(fail_log_path)
    pass_log_lines = read_log_file(pass_log_path)

    today_fail_lines = filter_by_today(fail_log_lines)
    today_pass_lines = filter_by_today(pass_log_lines)

    total_parsed, total_passed, total_failed = count_metrics(
        today_fail_lines, today_pass_lines)

    return total_parsed, total_passed, total_failed


def slack_notify_webhook(message, outcome, webhook_url) -> None:
    """
    Send notification to given Slack channel using a webhook

    Parameters
    ----------
    message : str
        Message to send to Slack.
    outcome : str
        "success" or "fail" to determine message color.
    webhook_url : str
        Webhook URL to send message to.
    """
    log.info("Sending message to Slack via webhook")

    if outcome == 'success':
        message = f":white_check_mark: {message}"
    elif outcome == 'fail':
        message = f":warning: {message}"
    else:
        log.error(f"Invalid outcome {outcome} provided for slack notification")
        message = f":warning: Error Invalid outcome {outcome} - {message}"

    payload = {
        "text": message
    }

    try:
        http = Session()
        retries = Retry(total=5, backoff_factor=5, allowed_methods=['POST'])
        http.mount("https://", HTTPAdapter(max_retries=retries))
        response = http.post(webhook_url,
                             data=json.dumps(payload),
                             headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Raise an exception for HTTP errors
        if response.status_code != 200:
            log.error(f"Error in sending slack notification: {response.text}")
        else:
            log.info("Successfully sent slack notification")
        return response
    except Exception as err:
        log.error(
            f"Error in sending post request for slack notification: {err}"
            )
        print(err)
        raise err


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
    Outputs:
        Generates slack notification based on the outcome of the job.
        Using the Slack API.
    """

    if parsed_args.channel == 'egg-test':
        script_name = ':mailbox: automated-workbook-parsing - Testing :test_tube:'
    else:
        script_name = ':mailbox: automated-workbook-parsing'
    # Chnage webhook URL depending on the channel
    if parsed_args.channel == 'egg-test':
        SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_TEST')
    elif parsed_args.channel == 'egg-logs':
        SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_LOGS')
    elif parsed_args.channel == 'egg-alerts':
        SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_ALERTS')
    else:
        raise ValueError("Invalid channel provided for slack notification")
    # Logic to handle different messages
    if outcome == 'success':
        total_parsed, total_passed, total_failed = collate_wb_info(
            parsed_args.fail_log_path, parsed_args.pass_log_path
        )
        if total_failed > 0:
            message = (
                f"{script_name}\n"
                f"Automated parsing has successfully run.\n"
                f":black_small_square: {total_parsed} workbooks parsed\n"
                f":black_small_square: {total_passed} passed\n"
                f":black_small_square: {total_failed} failed\n"
            )
            slack_notify_webhook(message, 'fail', SLACK_WEBHOOK_URL)
        elif total_parsed == total_passed:
            message = (
                f"{script_name}\n"
                f"Automated parsing has successfully run.\n"
                f":black_small_square: {total_parsed} workbooks parsed\n"
                f":black_small_square: {total_passed} passed\n"
                f":black_small_square: {total_failed} failed\n"
                "These workbooks require manual intervention.\n"
            )
            slack_notify_webhook(message, 'success', SLACK_WEBHOOK_URL)
        else:
            log.error("Invalid state to send slack notification")
            slack_notify_webhook(message, 'success', SLACK_WEBHOOK_URL)
    elif outcome == 'fail':
        message = f"Automated parsing of workbooks failed.\n Please check error logs. \n"
        slack_notify_webhook(message, 'fail', SLACK_WEBHOOK_URL)
    else:
        log.error("Invalid outcome provided for slack notification")
        message = (
            f"{script_name}\n"
            f"Error with Workbook parsing invalid outcome.\n"
            f"Please check run.\n"
            f"Please check logs for more information."
        )
        slack_notify_webhook(message, 'fail', SLACK_WEBHOOK_URL)


def main():
    """
    Main function to run the script.
    """
    parsed_args = parse_args()
    if parsed_args.channel == 'egg-test':
        log.info("Running in testing mode")
    coordinate_notifications(parsed_args, parsed_args.outcome)


if __name__ == "__main__":
    main()
