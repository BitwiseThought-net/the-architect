import os
import importlib
from lib.logger import log_action, log_text, log_warn, log_error
from lib.utils import update_heartbeat

def validate_loaders(knowledge_files):
    """Checks if loaders exist for all file types found in knowledge directory."""
    loaders_dir = "loaders"
    
    # Safety Check: If loaders folder is missing or empty
    if not os.path.exists(loaders_dir) or not os.listdir(loaders_dir):
        if knowledge_files:
            log_warn("Loaders directory is missing or empty. Knowledge files cannot be processed.")
        return set()

    missing_loaders = set()
    for file in knowledge_files:
        if os.path.isdir(os.path.join("knowledge", file)): continue
        ext = os.path.splitext(file)[1].lower().replace('.', '')
        if not ext: continue
        
        if not os.path.exists(os.path.join(loaders_dir, f"{ext}.py")):
            missing_loaders.add(ext)
            
    if missing_loaders:
        log_warn(f"Missing loaders for: {', '.join(missing_loaders)}. Skipping these files.")
    return missing_loaders

def get_all_knowledge_sources():
    knowledge_dir = "knowledge"
    
    # Safety Check: If knowledge folder is missing or empty
    if not os.path.exists(knowledge_dir):
        log_warn(f"Knowledge directory '{knowledge_dir}' not found.")
        return []

    files = [f for f in os.listdir(knowledge_dir) if not f.startswith('.')]
    if not files:
        log_text("No knowledge files found in /knowledge.")
        return []

    missing = validate_loaders(files)
    log_action("Scanning /knowledge directory for new sources...")
    sources = []

    for file in files:
        update_heartbeat()
        file_path = os.path.join(knowledge_dir, file)
        if os.path.isdir(file_path): continue
        
        ext = os.path.splitext(file)[1].lower().replace('.', '')
        if not ext or ext in missing: continue

        try:
            loader_module = importlib.import_module(f"loaders.{ext}")
            source = loader_module.get_source(file_path)
            if source:
                sources.append(source)
                log_text(f"Successfully loaded {file} using '{ext}' loader.")
        except Exception as e:
            log_error(f"Error loading {file} with '{ext}' loader: {str(e)}")

    log_text(f"Total knowledge sources identified: {len(sources)}")
    log_action("Knowledge sync complete.")
    return sources
