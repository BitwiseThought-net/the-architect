from crewai_tools import EXECTool

def get_tools():
    """
    Returns a standard execution tool that allows the agent 
    to run any shell command within the container.
    """
    return [EXECTool()]
