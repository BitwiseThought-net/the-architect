# test_discord.py
from io import discord
import sys

print("Firing immediate direct network test payload to Discord API...")
success = discord.broadcast_status("Test Connection: The Architect communication pipeline is operational.")
if success:
    print("✅ Success! Check your Discord channel.")
else:
    print("❌ Failure. Check your BOT_TOKEN or CHANNEL_ID credentials.")
