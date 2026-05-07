import os
import subprocess
from crewai_tools import tool

@tool("safe_terminal_exec")
def safe_terminal_exec(command: str):
    """
    Executes Python or Pytest commands strictly within the /app/output directory.
    Usage: 'pytest test_file.py' or 'python script.py'
    """
    safe_dir = "/app/output"

    # Security Check: Only allow python or pytest
    allowed_prefixes = ["python ", "pytest ", "python3 "]
    if not any(command.startswith(p) for p in allowed_prefixes):
        return "❌ Error: Only 'python' and 'pytest' commands are allowed for security."

    # Security Check: Prevent path traversal
    if ".." in command or "/" in command:
        return "❌ Error: Path traversal or absolute paths are forbidden. Stay in the local directory."

    try:
        # Run the command inside the safe directory
        result = subprocess.run(
            command,
            shell=True,
            cwd=safe_dir,
            capture_output=True,
            text=True,
            timeout=30 # Prevent infinite loops
        )

        output = result.stdout if result.stdout else ""
        errors = result.stderr if result.stderr else ""

        return f"--- Command Output ---\n{output}\n--- Errors ---\n{errors}"

    except Exception as e:
        return f"❌ Execution failed: {str(e)}"

def get_tools():
    return [safe_terminal_exec]
