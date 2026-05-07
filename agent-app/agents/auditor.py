from crewai import Agent
import os

def get_agent(tools=None):
    """
    Agent specialized in code security, vulnerability detection, and compliance.
    """
    return Agent(
        role="Cybersecurity Auditor",
        goal="Review research and proposed code for security vulnerabilities, injection risks, and data leaks.",
        backstory="""You are a senior security researcher with an obsession for 'Zero Trust' architecture. 
        You specialize in identifying OWASP top 10 risks and ensuring that any generated code 
        is hardened against common exploits.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        tools=tools or [],
        memory=True,
        verbose=True
    )
