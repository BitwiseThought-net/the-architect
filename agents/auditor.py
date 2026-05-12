from ai_layer.orchestrator import Agent, LLM
import os
from lib.utils import get_config_value

def get_agent(tools=None, model_name=None):
    # Fallback order: Passed argument -> config.json -> hardcoded default
    target_model = model_name or get_config_value("MODEL_NAME", "llama3:latest")
    local_llm = LLM(
        model=f"ollama/{target_model}",
        base_url=get_config_value("LITELLM_URL", "http://ai-litellm:4000/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-local-1234"),
        temperature=float(get_config_value("TEMPERATURE", 0.3)),
        max_tokens=4096
    )
    return Agent(
        role="Cybersecurity Auditor",
        goal="Review research and proposed code for security vulnerabilities, injection risks, and data leaks.",
        backstory="""You are a senior security researcher with an obsession for 'Zero Trust'
        architecture. You specialize in identifying OWASP top 10 risks and ensuring
        that any generated code is hardened against common exploits.""",
        llm=local_llm,
        tools=tools or [],
        memory=True,
        verbose=True
    )
