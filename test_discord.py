# test_discord.py
import sys
import os

# 1. Standardize lookups so Python doesn't collide with native libraries
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 2. Import the centralized utility function and the dynamic channel module
from lib.utils import get_config_value
from ai_io import discord

print("=== CONFIGURATION FILE VERIFICATION CHECK ===")
# Dynamically fetch values right out of the central container config.json
project_name = get_config_value("PROJECT_NAME")
target_model = get_config_value("MODEL_NAME")

print(f"📦 Active Project Identity: {project_name}")
print(f"🤖 Loaded Swarm Core Model: {target_model}")
print("---------------------------------------------")

print("Firing absolute network test payload via ai_io/discord.py...")
# Execute the direct API pass-through using your verified REST pathway
success = discord.broadcast_status(
    f"Test Status Update: System central lookup operational for project '{project_name}'."
)

if success:
    print("✅ Success! Payload cleanly delivered to the Discord server channel.")
else:
    print("❌ Failure. Discord rejected the request. Check token allocations.")
