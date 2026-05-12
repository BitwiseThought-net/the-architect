import os
import importlib
from lib.utils import get_config_value
from lib.logger import log_action, log_error

# 1. Discover the active framework target from config.json with an environment fallback
FRAMEWORK = get_config_value("AI_FRAMEWORK", os.getenv("AI_FRAMEWORK", "crewai")).lower()

# Validate that the selected framework engine is supported by the architecture
available_frameworks = ["crewai", "autogen", "langgraph", "smolagents"]
if FRAMEWORK not in available_frameworks:
    log_error(f"Framework '{FRAMEWORK}' not implemented. Falling back to crewai.")
    FRAMEWORK = "crewai"

try:
    # 2. Dynamically import the specific interface factory file
    _module = importlib.import_module(f"ai_layer.{FRAMEWORK}")
    
    # 3. Expose the standard core framework primitives to the application layer
    Agent = _module.Agent
    Task = _module.Task
    Crew = _module.Crew
    LLM = _module.LLM
    tool = _module.tool
    
    # Optional execution modifiers (safely returns None if not present in target engine)
    Process = getattr(_module, "Process", None)
    
    # 4. Expose framework-agnostic tool definitions and knowledge sources
    Knowledge = getattr(_module, "Knowledge", None)
    FileReadTool = getattr(_module, "FileReadTool", None)
    FileWriterTool = getattr(_module, "FileWriterTool", None)
    EXECTool = getattr(_module, "EXECTool", None)
    DuckDuckGoSearchTool = getattr(_module, "DuckDuckGoSearchTool", None)
    
    log_action(f"🤖 Unified AI Layer successfully bound to backend: {FRAMEWORK}")

except Exception as e:
    log_error(f"Critical boot error: Failed to instantiate abstraction layer for '{FRAMEWORK}': {e}")
    raise e
