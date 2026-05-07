import os
import requests
from crewai_tools import tool

@tool("send_notification")
def send_notification(message: str):
    """
    Sends a message to Slack or Discord.
    Gracefully handles missing webhook URLs.
    """

    url = os.getenv("NOTIFY_WEBHOOK_URL")

    if not url or url.strip() == "":
        return "⚠️ Notification skipped: NOTIFY_WEBHOOK_URL is not set in .env"

    payload = {"text": f"🚨 *Agent Approval Required:* \n{message}"}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status() # Raise error for bad status codes
        return f"✅ Notification sent! (Status: {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"❌ Failed to send notification: {str(e)}"

def get_tools():
    return [send_notification]
