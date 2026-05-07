from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

def get_source(file_paths):
    """
    Loads YAML files as text. This preserves the indentation structure, 
    which is critical for the LLM to understand nested YAML configurations.
    """
    return TextFileKnowledgeSource(file_paths=file_paths)
