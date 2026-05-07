from crewai.knowledge.source.json_knowledge_source import JSONKnowledgeSource

def get_source(file_paths):
    return JSONKnowledgeSource(file_paths=file_paths)
