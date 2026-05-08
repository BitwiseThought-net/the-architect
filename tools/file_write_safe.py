import os
from crewai_tools import FileWriterTool

def get_tools():
    """
    Returns a hardened FileWriterTool that restricts writing
    to the /app/output directory.
    """
    # Force all writes to go into the 'output' subdirectory
    safe_dir = "/app/output"
    if not os.path.exists(safe_dir):
        os.makedirs(safe_dir)

    return [FileWriterTool(dir_path=safe_dir)]
