from crewai_tools import DuckDuckGoSearchTool

def get_tools():
    # Returns a list of tools because an agent might need multiple
    return [DuckDuckGoSearchTool()]
