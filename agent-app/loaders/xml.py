from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

def get_source(file_paths):
    # We treat XML/SOAP as text so the LLM can parse the tag structure
    return TextFileKnowledgeSource(file_paths=file_paths)
