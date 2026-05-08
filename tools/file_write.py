from crewai_tools import FileWriterTool

def get_tools():
    """
    Returns the FileWriterTool to allow agents to write or update local files.
    """
    return [FileWriterTool()]
