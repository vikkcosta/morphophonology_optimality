from configuration import Configuration
from feature_table import FeatureTable
from math import ceil, log
import requests
import json
from pathlib import Path
import pathlib
import os
from debug_tools import is_local_machine
flags_dir = pathlib.Path.cwd().joinpath("flags")


def send_to_webhook(message):
    if is_local_machine():
        return
    webhook_url = "https://hooks.slack.com/services/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"
    icon_emoji = ":robot_face:"

    full_payload = {"channel": "opt-phopho-bot",
                    "username": "Notification",
                    "text":message,
                    "icon_emoji": icon_emoji}

    full_payload_json = json.dumps(full_payload)
    response = requests.post(webhook_url, data=full_payload_json, headers={'Content-Type': 'application/json'})

    if response.status_code != 200:
        print("Webhook failed")  # maybe send email to someone?


def set_configuration(configuration_key, value):
    configurations = Configuration()
    configurations[configuration_key] = value


def get_configuration(configuration_key):
    configurations = Configuration()
    return configurations[configuration_key]


def get_feature_table():
    return FeatureTable.get_instance()


def get_weighted_list(weighted_choices):  # adds an element as it's weight number
    return [value for value, counter in weighted_choices for _ in range(counter)]


def ceiling_of_log_two(x: int):
    return ceil(log(x, 2))

