from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
# Raw notes, logs
def get_source(file_paths):
    return TextFileKnowledgeSource(file_paths=file_paths)
