import os
import importlib

KNOWLEDGE_DIR = "knowledge"
LOADERS_PKG = "loaders"

def get_all_knowledge_sources():
    # Group files by extension: { 'pdf': ['.../a.pdf'], 'txt': ['.../b.txt'] }
    files_by_ext = {}

    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)

    for filename in os.listdir(KNOWLEDGE_DIR):
        name, ext = os.path.splitext(filename)
        if not ext:
            continue

        # Normalize: '.PDF' -> 'pdf', '.txt' -> 'txt'
        ext_clean = ext.lower().replace('.', '')
        path = os.path.join(KNOWLEDGE_DIR, filename)

        files_by_ext.setdefault(ext_clean, []).append(path)

    sources = []
    for ext, paths in files_by_ext.items():
        try:
            # Dynamically look for loaders/pdf.py, loaders/txt.py, etc.
            module = importlib.import_module(f"{LOADERS_PKG}.{ext}")
            sources.append(module.get_source(file_paths=paths))
            print(f"✅ Loaded {len(paths)} files using {ext}.py loader")
        except ImportError:
            # If no loader exists for that extension, we just skip it
            print(f"⚠️  No loader found for '.{ext}' (checked {LOADERS_PKG}/{ext}.py)")
            continue

    return sources
