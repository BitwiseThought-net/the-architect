import os
import sys
import importlib.util

# Direct path import for logger to bypass ModuleNotFoundError
spec = importlib.util.spec_from_file_location("logger", "/app/lib/logger.py")
logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logger)
log_action, log_text, log_warn, log_error = logger.log_action, logger.log_text, logger.log_warn, logger.log_error

import importlib

def get_all_knowledge_sources():
    knowledge_dir = "knowledge"
    loaders_dir = "loaders"
    sources = []

    if not os.path.exists(knowledge_dir):
        log_warn(f"Knowledge directory '{knowledge_dir}' not found. Creating it...")
        os.makedirs(knowledge_dir)
        return sources

    log_action("Scanning /knowledge directory for new sources...")

    files = os.listdir(knowledge_dir)
    if not files:
        log_text("No files found in /knowledge.")
        return sources

    for file in files:
        file_path = os.path.join(knowledge_dir, file)
        # Extract extension (e.g., '.pdf' -> 'pdf')
        ext = os.path.splitext(file).lower().replace('.', '')

        if not ext:
            log_warn(f"Skipping file with no extension: {file}")
            continue

        try:
            # Dynamically import the loader matching the extension
            loader_module_name = f"loaders.{ext}"
            loader_module = importlib.import_module(loader_module_name)

            # Assumes every loader has a get_source(file_path) function
            source = loader_module.get_source(file_path)

            if source:
                sources.append(source)
                log_text(f"Successfully loaded {file} using '{ext}' loader.")
            else:
                log_warn(f"Loader '{ext}' returned no source for {file}.")

        except ImportError:
            log_warn(f"No custom loader found for '.{ext}' files. Missing {loaders_dir}/{ext}.py")
        except Exception as e:
            log_error(f"Error loading {file} with '{ext}' loader: {str(e)}")

    log_text(f"Total knowledge sources identified: {len(sources)}")
    log_action("Knowledge sync complete.")
    return sources

