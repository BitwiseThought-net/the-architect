import os
from ai_layer.orchestrator import Knowledge

def get_source(file_path):
    """
    Initializes and returns a framework-agnostic XML Knowledge Source.
    Uses the underlying framework's mapped XML processor from the orchestrator.
    """
    if not os.path.exists(file_path):
        return None

    # Extract just the raw filename for cleanly naming the collection slice inside the DB
    file_name = os.path.basename(file_path)

    # Safely query the abstract factory for the XML class implementation
    if Knowledge and hasattr(Knowledge, "XML"):
        return Knowledge.XML(
            file_path=file_path,
            metadata={"source": file_name, "type": "xml"}
        )

    return None
