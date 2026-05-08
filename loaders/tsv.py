from crewai.knowledge.source.csv_knowledge_source import CSVKnowledgeSource

def get_source(file_paths):
    # CSVKnowledgeSource typically handles common delimiters
    return CSVKnowledgeSource(file_paths=file_paths)
