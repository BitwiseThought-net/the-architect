import os
from knowledge_manager import get_all_knowledge_sources
from lib.logger import log_action, log_text, log_error

def sync_knowledge_base():
    log_action("Starting Knowledge Base Ingestion...")

    try:
        sources = get_all_knowledge_sources()

        if not sources:
            log_text("No new files to ingest. Knowledge base is up to date.")
            return

        log_text(f"Preparing to index {len(sources)} sources into ChromaDB...")

        for source in sources:
            log_text(f"Processing source: {source.file_paths}")

        log_action("Ingestion check complete.")

    except Exception as e:
        log_error(f"Failed to ingest knowledge: {str(e)}")

if __name__ == "__main__":
    sync_knowledge_base()
