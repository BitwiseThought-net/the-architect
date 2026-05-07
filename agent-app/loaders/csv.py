from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource

def get_source(file_paths):
    return CSVKnowledgeSource(file_paths=file_paths)
