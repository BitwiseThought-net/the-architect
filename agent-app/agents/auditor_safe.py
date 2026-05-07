from crewai import Agent
import os

def get_agent(tools=None):
    return Agent(
        role="Cybersecurity Auditor",
        goal="""Review code for vulnerabilities and verify that all file operations 
        are directed toward the allowed '/app/output' directory.""",
        backstory="""You are a strict security officer. You never allow agents to 
        write files outside of the designated output folder. You flag any 
        attempt to use absolute paths or '..' navigation.""",
        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://litellm:4000/v1",
        tools=tools or [],
        memory=True,
        verbose=True
    )
