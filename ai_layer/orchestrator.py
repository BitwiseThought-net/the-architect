import os
import importlib
from lib.utils import get_config_value
from lib.logger import log_action, log_error

# Discover the active framework target purely via central utilities configuration handles
FRAMEWORK = get_config_value("AI_FRAMEWORK", "crewai").lower()

if not FRAMEWORK:
    log_error(f"Framework '{FRAMEWORK}' not specified. Falling back to crewai.")
    FRAMEWORK = "crewai"

try:
    _module = importlib.import_module(f"ai_layer.{FRAMEWORK}")

    Agent = _module.Agent
    Task = _module.Task
    Crew = _module.Crew
    LLM = _module.LLM
    tool = _module.tool
    Process = getattr(_module, "Process", None)

    Knowledge = getattr(_module, "Knowledge", None)
    FileReadTool = getattr(_module, "FileReadTool", None)
    FileWriterTool = getattr(_module, "FileWriterTool", None)
    EXECTool = getattr(_module, "EXECTool", None)
    DuckDuckGoSearchTool = getattr(_module, "DuckDuckGoSearchTool", None)

    log_action(f"🤖 Unified AI Layer successfully bound to backend: {FRAMEWORK}")

except Exception as e:
    log_error(f"Critical boot error: Failed to instantiate abstraction layer for '{FRAMEWORK}': {e}")
    raise e
