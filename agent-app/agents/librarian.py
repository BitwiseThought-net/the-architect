from crewai import Agent, LLM
import os

def get_agent(tools=None):
    local_llm = LLM(
        model=f"ollama/{os.getenv('MODEL_NAME')}",
        base_url="http://agent-litellm:4000/v1",
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234")
    )

    return Agent(
        role="System Librarian",
        goal="Ensure all local documentation is properly indexed and available for the team.",
        backstory="""You are the gatekeeper of knowledge. You scan the knowledge 
        directory for new materials, organize them, and ensure the team 
        is working with the most up-to-date data.""",
#        llm=f"openai/ollama/{os.getenv('MODEL_NAME')}",
#        llm=f"ollama/{os.getenv('MODEL_NAME')}",
        llm=local_llm,
        base_url="http://litellm:4000/v1",
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
