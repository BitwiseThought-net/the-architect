from crewai import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback order: Passed argument -> config.json -> hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "mistral:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://agent-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Documentation Specialist",
        goal="Retrieve, cross-reference, and summarize technical information from local docs and the web.",
        backstory="""You are a meticulous researcher with expertise in technical RAG systems.
        You excel at finding hidden details in local PDFs and validating them against live web data.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
