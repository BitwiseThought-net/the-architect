from crewai import Agent
import os

def get_agent(tools=None):
    """
    Agent specialized in software development and optimization.
    """
    return Agent(
        role="Senior Software Engineer",
        goal="Transform technical requirements and research findings into clean, efficient Python code.",
        backstory="""You are a master of Python development and containerized architecture. 
        You focus on writing modular, well-documented code that adheres to best practices. 
        You are highly skilled at analyzing existing codebases to provide optimizations.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        tools=tools or [],              # Dynamically loaded from tools/ folder
        memory=True,                     # Enables long-term/short-term memory usage
        verbose=True
    )
