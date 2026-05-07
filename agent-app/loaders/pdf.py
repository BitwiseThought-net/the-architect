from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
# Research papers, manuals
def get_source(file_paths):
    return PDFKnowledgeSource(file_paths=file_paths)
