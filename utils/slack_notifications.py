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

log = logging.getLogger("monitor log")
log.setLevel(logging.DEBUG)

log_format = logging.StreamHandler(sys.stdout)
log_format.setFormatter(
    logging.Formatter(
        "%(asctime)s:%(module)s:%(levelname)s: %(message)s"
    )
)

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
        '--message', help="message to send", type=str, required=True
    )
    parser.add_argument(
        '--channel', help="Slack channel to send notification to",
        type=str, required=True
    )
    parser.add_argument(
        '--outcome', help="outcome of job", type=str, required=True
    )
    return parser.parse_args()

def slack_notify(channel, message, outcome) -> None:
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

if __name__ == "__main__":
    parsed_args = parse_args()

    slack_notify(
        parse_args().channel,
        parse_args().message,
        parse_args().outcome
    )