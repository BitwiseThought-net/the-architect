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
        goal="Review research and proposed code for security vulnerabilities, injection risks, and data leaks.",
        backstory="""You are a senior security researcher with an obsession for 'Zero Trust' architecture. 
        You specialize in identifying OWASP top 10 risks and ensuring that any generated code 
        is hardened against common exploits.""",
#        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
#        llm=f"ollama/{os.getenv('MODEL_NAME')}",
        llm=local_llm,
        base_url="http://litellm:4000/v1",
        tools=tools or [],
        memory=True,
        verbose=True
    )
