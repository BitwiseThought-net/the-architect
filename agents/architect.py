from ai_layer.orchestrator import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback order: Passed argument -> config.json -> hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "codellama:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Solution Architect",
        goal="Design scalable, modular, and efficient system structures based on requirements.",
        backstory="""You are a veteran systems designer. You focus on the big picture,
        ensuring that code follows SOLID principles and that the chosen tech stack
        aligns with the project's long-term scalability and maintenance goals.""",
        llm=local_llm,
        allow_knowledge_retrieval=True,
        tools=tools or [],
        memory=True,
        verbose=True
    )
