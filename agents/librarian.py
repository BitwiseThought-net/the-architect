from crewai import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback to config.json, then to a hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "mistral:latest")

    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://agent-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )

    return Agent(
        role="System Librarian",
        goal="Ensure all local documentation is properly indexed and available for the team.",
        backstory="""You are the gatekeeper of knowledge. You scan the knowledge directory 
        for new materials, organize them, and ensure the team is working with the most 
        up-to-date data.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True, # Librarian needs memory to track indexing state
        verbose=True
    )
