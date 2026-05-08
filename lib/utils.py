import os
import json
import time
import signal
from lib.logger import log_error

# --- HEARTBEAT ---
def update_heartbeat():
    """Updates a file timestamp so Docker/Autoheal knows the process is alive."""
    try:
        with open('/tmp/heartbeat', 'w') as f:
            f.write(str(time.time()))
    except Exception as e:
        # Using print to avoid logger circular dependency
        print(f"Heartbeat update failed: {e}")

# --- TIMEOUT ---
def timeout_handler(signum, frame):
    raise TimeoutError("Mission execution timed out.")

def set_mission_timeout(seconds):
    """Sets a hard Linux signal alarm for the current process."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def clear_mission_timeout():
    """Cancels the active signal alarm."""
    signal.alarm(0)

# --- CONFIG ---
def get_config_value(key, default=None):
    """Reads config.json on demand to allow live updates without restarts."""
    try:
        if not os.path.exists('config.json'):
            return default
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get(key, default)
    except Exception as e:
        log_error(f"Error reading config.json: {e}")
        return default
