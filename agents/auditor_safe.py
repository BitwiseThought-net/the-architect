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
        goal="""Review code for vulnerabilities and verify that all file operations
        are directed toward the allowed '/app/output' directory.""",
        backstory="""You are a strict security officer. You never allow agents to
        write files outside of the designated output folder. You flag any attempt
        to use absolute paths or '..' navigation.""",
        llm=local_llm,
        tools=tools or [],
        memory=True,
        verbose=True
    )
