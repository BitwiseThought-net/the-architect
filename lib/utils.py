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
        # Using print to avoid potential circular logger issues during system tasks
        print(f"Heartbeat update failed: {e}")

# --- TIMEOUT ---
def timeout_handler(signum, frame):
    """Callback triggered by signal.alarm when execution time is exceeded."""
    raise TimeoutError("Mission execution timed out.")

def set_mission_timeout(seconds):
    """Sets a hard Linux signal alarm for the current process."""
    if seconds and int(seconds) > 0:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds))

def clear_mission_timeout():
    """Cancels any active signal alarm."""
    signal.alarm(0)

# --- CONFIG ---
def get_config_value(key, default=None):
    """
    Reads config.json on demand to allow live updates without restarts.
    Prioritizes config.json, then Environment Variables, then the provided default.
    """
    val = None
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
                if key in config:
                    val = config[key]
                else:
                    val = os.getenv(key)
        else:
            val = os.getenv(key)
    except Exception as e:
        log_error(f"Error reading config.json: {e}")
        val = os.getenv(key)

    # Use default if no value was found in JSON or ENV
    if val is None:
        return default

    # Auto-cast common numeric strings from ENV fallbacks to ensure library compatibility
    if isinstance(val, str) and val.isdigit():
        return int(val)

    return val
