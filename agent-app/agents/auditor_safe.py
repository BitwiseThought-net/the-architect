from crewai import Agent, LLM
import os

def get_agent(tools=None):
    local_llm = LLM(
        model=f"ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )

    return Agent(
        role="Cybersecurity Auditor",
        goal="""Review code for vulnerabilities and verify that all file operations 
        are directed toward the allowed '/app/output' directory.""",
        backstory="""You are a strict security officer. You never allow agents to 
        write files outside of the designated output folder. You flag any 
        attempt to use absolute paths or '..' navigation.""",
#        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
#        llm=f"ollama/{os.getenv('MODEL_NAME')}",
        llm=local_llm,
        base_url="http://litellm:4000/v1",
        tools=tools or [],
        memory=True,
        verbose=True
    )
