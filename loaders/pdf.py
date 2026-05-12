from ai_layer.orchestrator import Knowledge
import os

def get_source(file_path):
    filename = os.path.basename(file_path)
    return PDFKnowledgeSource(file_paths=[filename])
