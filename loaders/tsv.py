import os
from ai_layer.orchestrator import Knowledge

def get_source(file_path):
    """
    Initializes and returns a framework-agnostic TSV Knowledge Source.
    Uses the underlying framework's mapped TextFile processor from the orchestrator.
    """
    if not os.path.exists(file_path):
        return None

    file_name = os.path.basename(file_path)

    if Knowledge and hasattr(Knowledge, "TextFile"):
        return Knowledge.TextFile(
            file_path=file_path,
            metadata={"source": file_name, "type": "tsv"}
        )

    return None
