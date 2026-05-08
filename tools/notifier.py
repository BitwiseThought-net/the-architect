import os
import requests
from crewai_tools import tool
from lib.utils import get_config_value

@tool("send_notification")
def send_notification(message: str):
    """ Sends a message to Slack or Discord. Gracefully handles missing webhook URLs. """
    # Re-read from config.json to allow webhook URL updates without restarts
    url = get_config_value("NOTIFY_WEBHOOK_URL", os.getenv("NOTIFY_WEBHOOK_URL"))

    if not url or url.strip() == "":
        return "⚠️ Notification skipped: NOTIFY_WEBHOOK_URL is not set in config.json or .env"

    payload = {"text": f"🚨 *Agent Alert:* \n{message}"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return f"✅ Notification sent! (Status: {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"❌ Failed to send notification: {str(e)}"

def get_tools():
    return [send_notification]
