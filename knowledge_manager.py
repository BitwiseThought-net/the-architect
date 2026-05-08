import os
import importlib
from lib.logger import log_action, log_text, log_warn, log_error

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
        # Important: file is just the name (e.g., 'mission_brief.txt')
        # We only join for the existence check and extension extraction
        file_path = os.path.join(knowledge_dir, file)
        
        if os.path.isdir(file_path):
            continue

        ext = os.path.splitext(file)[1].lower().replace('.', '')
        
        if not ext:
            log_warn(f"Skipping file with no extension: {file}")
            continue

        try:
            loader_module_name = f"loaders.{ext}"
            loader_module = importlib.import_module(loader_module_name)
            
            # Pass the full relative path from the app root: 'knowledge/filename.ext'
            # If your loaders expect a list, we wrap it here.
            source = loader_module.get_source([file_path])
            
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
