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
    Checks config_mount first (stable directory mount), then the local root,
    then Environment Variables.
    """
    paths = ['config_mount/config.json', 'config.json']
    val = None

    for path in paths:
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    config = json.load(f)
                    if key in config:
                        val = config[key]
                        break
        except Exception:
            continue

    if val is None:
        val = os.getenv(key)

    if val is None:
        return default

    if isinstance(val, str) and val.isdigit():
        return int(val)
    return val

# --- PLUGIN SYSTEM ---
def get_active_plugins():
    """
    Scans the plugins/ directory for .json files on-demand.
    Returns a dict: { "feature_name": { "settings": {}, "enabled_for": [] } }
    """
    # Check both mount point and local directory
    plugin_dirs = ['config_mount/plugins', 'plugins']
    active_features = {}

    for p_dir in plugin_dirs:
        if not os.path.exists(p_dir):
            continue

        try:
            for filename in sorted(os.listdir(p_dir)):
                if filename.endswith('.json'):
                    path = os.path.join(p_dir, filename)
                    with open(path, 'r') as f:
                        try:
                            data = json.load(f)
                            feature = data.get("feature")
                            # Only return if explicitly enabled
                            if feature and data.get("enabled") is True:
                                active_features[feature] = {
                                    "settings": data.get("settings", {}),
                                    "enabled_for": data.get("enabled_for", ["*"]) # Default to all if missing
                                }
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log_error(f"Error scanning plugins in {p_dir}: {e}")
    return active_features
