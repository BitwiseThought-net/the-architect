from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

def get_source(file_path):
    # file_path is already 'knowledge/filename.txt'
    return TextFileKnowledgeSource(file_paths=[file_path])
