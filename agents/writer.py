from crewai import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback order: Passed argument -> config.json -> hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "llama3:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://agent-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Technical Content Strategist",
        goal="Produce high-quality, clear, and professional documentation for all project components.",
        backstory="""You are a world-class technical writer. You specialize in
        translating complex code and architectural patterns into user-friendly
        documentation, including READMEs, API guides, and system manuals.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
