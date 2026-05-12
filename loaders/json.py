import os
from ai_layer.orchestrator import Knowledge

def get_source(file_path):
    """
    Initializes and returns a framework-agnostic JSON Knowledge Source.
    Uses the underlying framework's mapped JSON processor from the orchestrator.
    """
    if not os.path.exists(file_path):
        return None

    file_name = os.path.basename(file_path)

    if Knowledge and hasattr(Knowledge, "JSON"):
        return Knowledge.JSON(
            file_path=file_path,
            metadata={"source": file_name, "type": "json"}
        )

    return None
