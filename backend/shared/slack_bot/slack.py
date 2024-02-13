import os
import slack_sdk

CHANNEL = "#auto-repurpose"

access_token = os.environ.get("SLACK_ACCESS_TOKEN")

slack_web_client = slack_sdk.WebClient(token=access_token)

KNOWN_ACCOUNTS = {}


def send_slack_message(message):
    if not access_token:
        return

    # Replace known account_ids in the message
    for account_id, name in KNOWN_ACCOUNTS.items():
        message = message.replace(account_id, name)

    try:
        slack_web_client.chat_postMessage(channel=CHANNEL, text=message)
    except Exception as exc:
        print("Error sending message to Slack", exc)
