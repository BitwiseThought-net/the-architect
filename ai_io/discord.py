import requests
from ai_layer.orchestrator import tool
from lib.utils import get_config_value

# --- PLUGIN METADATA ---
INFO = {
    "instructions": [
        "1. Go to Discord Developer Portal (https://discord.com).",
        "2. Create 'New Application' named Agent-Smith.",
        "3. Go to 'Bot' tab: Reset/Copy Token into 'bot_token' in SETTINGS below.",
        "4. Enable 'Message Content Intent' under Privileged Gateway Intents.",
        "5. Go to 'OAuth2' -> 'URL Generator': Select scopes 'bot' and 'applications.commands'.",
        "6. Select Permissions: 'Send Messages', 'Read Message History', 'Use Slash Commands'.",
        "7. Use generated URL to invite the bot to your server.",
        "8. Enable Developer Mode in Discord (User Settings -> Advanced).",
        "9. Right-click Server for 'server_id' and target Channel for 'channel_id'."
    ]
}

# --- PLUGIN SETTINGS ---
# Default is empty. If values are provided here, they take absolute priority over central config.
SETTINGS = {
    "BOT_TOKEN": "",
    "SERVER_ID": "",
    "CHANNEL_ID": "",
    "RESPONSE_PREFIX_ENABLED": True
}

def _send_msg(message: str) -> bool:
    """
    Centralized communication routing endpoint helper.
    Priority 1: Check local SETTINGS dictionary context first.
    Priority 2: Fall back dynamically to centralized get_config_value matrix lookups.
    """
    # 1. Resolve Bot Token
    bot_token = SETTINGS.get("BOT_TOKEN")
    print(f"A: bot_token:{bot_token}.")
    if not bot_token:
        bot_token = get_config_value("BOT_TOKEN")
    if not bot_token:
        return False

    # 2. Resolve Server ID (Guild ID)
    server_id = SETTINGS.get("SERVER_ID")
    print(f"B: bottoken:{bot_token}, server_id:{server_id}")
    if not server_id:
        server_id = get_config_value("SERVER_ID")
    if not server_id:
        return False

    # 3. Resolve Channel ID
    channel_id = SETTINGS.get("CHANNEL_ID")
    print(f"C: bot_token:{bot_token}, server_id:{server_id}, channel_id:{channel_id}.")
    if not channel_id:
        channel_id = get_config_value("CHANNEL_ID")
    if not channel_id:
        return False

    print(f"D: bot_token:{bot_token}, server_id:{server_id}, channel_id:{channel_id}.")
    # VERIFIED CORRECT REST API ENDPOINT: Absolute scheme, explicit version, and proper slashes
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    print(f"url:[{url}]")
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(url, headers=headers, json={"content": message}, timeout=10)
        return res.status_code in [200, 201]
    except Exception:
        return False

@tool("discord_interaction")
def discord_interaction(message: str):
    """Sends agent responses directly to the configured Discord channel using the Bot Token."""
    success = _send_msg(message)
    return "✅ Response successfully posted to Discord." if success else "❌ Discord API Error."

def broadcast_status(message: str) -> bool:
    """Dynamic interface endpoint executing direct message delivery."""
    return _send_msg(message)

def register():
    """Provides the tool and identity rules to the main service loader package."""
    prefix_enabled = SETTINGS.get("RESPONSE_PREFIX_ENABLED")
    if prefix_enabled is None:
        prefix_enabled = get_config_value("RESPONSE_PREFIX_ENABLED", True)

    return {
        "tools": [discord_interaction],
        "enabled_for": ["*"],
        "identity_prefix": bool(prefix_enabled)
    }
