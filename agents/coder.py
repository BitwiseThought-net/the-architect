from ai_layer.orchestrator import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Dynamic fallback: Use passed name, then config.json, then hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "codellama:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Senior Software Engineer",
        goal="Transform technical requirements and research findings into clean, efficient Python code.",
        backstory="""You are a master of Python development and containerized architecture.
        You focus on writing modular, well-documented code that adheres to best practices.
        You are highly skilled at analyzing existing codebases to provide optimizations.""",
        llm=local_llm,
        tools=tools or [],
        memory=True,
        verbose=True
    )
