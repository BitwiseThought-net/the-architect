from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

def get_source(file_paths):
    # Using TextFileKnowledgeSource allows the LLM to read raw code/logs
    return TextFileKnowledgeSource(file_paths=file_paths)
