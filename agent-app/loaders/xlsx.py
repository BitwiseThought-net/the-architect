from crewai.knowledge.source.excel_knowledge_source import ExcelKnowledgeSource

def get_source(file_paths):
    return ExcelKnowledgeSource(file_paths=file_paths)
